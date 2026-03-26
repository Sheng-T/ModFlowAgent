"""Web搜索和RAG增强工具 - 用于answer_general_question_node"""
import os
import re
import shutil
from typing import List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class TemporaryDocManager:
    """临时文档目录管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化临时文档管理器
        :param base_dir: 基础目录，默认在 static/temp
        """
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   "static", "temp")
        self.base_dir = base_dir
        self.session_dir = None
        self._create_session()
    
    def _create_session(self):
        """创建当前会话的临时目录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.base_dir, f"session_{timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)
    
    def get_html_dir(self) -> str:
        """获取HTML保存目录"""
        html_dir = os.path.join(self.session_dir, "html")
        os.makedirs(html_dir, exist_ok=True)
        return html_dir

    def get_markdown_path(self) -> str:
        """获取Markdown文件路径"""
        md_path = os.path.join(self.session_dir, "docs.md")
        return md_path
    
    def cleanup(self):
        """清理临时目录"""
        if self.session_dir and os.path.exists(self.session_dir):
            try:
                shutil.rmtree(self.session_dir)
            except Exception as e:
                print(f"[清理] 临时文件清理失败: {e}")


class WebSearcher:
    """Web搜索工具"""
    
    @staticmethod
    def search_duckduckgo(query: str, num_results: int = 5) -> List[dict]:
        """
        使用DuckDuckGo搜索（无需API密钥）
        需要: pip install ddgs
        """
        try:
            # 尝试导入新库 ddgs
            try:
                from ddgs import DDGS
            except ImportError:
                try:
                    # 备选：尝试旧库名（兼容性）
                    from duckduckgo_search import DDGS
                    print("  [警告] 检测到旧库 duckduckgo_search，建议升级: pip install ddgs")
                except ImportError:
                    print("\n【提示】搜索库未安装，请运行:")
                    print("  python utils/check_dependencies.py")
                    print("\n或手动安装:")
                    print("  pip install ddgs html2text beautifulsoup4")
                    print("\n不安装搜索库也可使用纯LLM回答。\n")
                    return []
            
            results = []
            try:
                # timeout 从 10s 改为 5s，更快失败 
                ddgs_session = DDGS(timeout=5)
                response = ddgs_session.text(query, max_results=num_results)
                
                count = 0
                for result in response:
                    if count >= num_results:
                        break
                    if isinstance(result, dict):
                        results.append({
                            "title": result.get("title", ""),
                            "url": result.get("href", "") or result.get("url", ""),
                            "snippet": result.get("body", "") or result.get("snippet", "")
                        })
                        count += 1
                
                if results:
                    print(f"  ✓ 搜索成功: 找到 {len(results)} 个结果")
                else:
                    print(f"  ✗ 搜索无结果")
                    
            except Exception as inner_e:
                print(f"  ✗ 搜索网络异常: {type(inner_e).__name__}")
            
            return results
            
        except Exception as e:
            print(f"  ✗ 搜索失败: {type(e).__name__}")
            return []
    
    @staticmethod
    def search_google_simple(query: str, num_results: int = 5) -> List[dict]:
        """
        简单的Google搜索备选方案（通过googlesearch库）
        """
        return []  # 当前不支持Google搜索，使用DuckDuckGo


class PageCrawler:
    """页面爬取工具"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout  # 增加到60秒，避免超时
        self.max_retries = max_retries
        self.last_error = None  # 存储最后的错误信息
        self.session = requests.Session()
        # 多样化 User-Agent，避免被反爬
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
        ]
        self.session.headers.update({
            'User-Agent': self.user_agents[0],
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def crawl_page(self, url: str, save_dir: str) -> Optional[str]:
        """
        爬取单个页面，捕获错误信息
        """
        import time
        import random
        from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
        
        self.last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 随机延迟 0.5-1.5 秒，模拟人工浏览
                time.sleep(random.uniform(0.5, 1.5))
                
                # 轮换 User-Agent
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.encoding = 'utf-8'
                response.raise_for_status()
                
                # 生成本地文件名
                parsed = urlparse(url)
                filename = parsed.path.split('/')[-1] or 'index'
                if not filename.endswith('.html'):
                    filename += '.html'
                
                os.makedirs(save_dir, exist_ok=True)
                local_path = os.path.join(save_dir, filename)
                
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                return local_path
                
            except Timeout:
                self.last_error = "超时"
            except ConnectionError:
                self.last_error = "网络连接失败"
            except HTTPError as e:
                self.last_error = f"HTTP{e.response.status_code}"
            except RequestException as e:
                self.last_error = type(e).__name__
            except Exception as e:
                self.last_error = type(e).__name__
        
        return None
    
    def crawl_pages(self, urls: List[str], save_dir: str) -> List[str]:
        """
        批量爬取页面，显示失败原因
        """
        results = []
        for i, url in enumerate(urls, 1):
            if url:
                display_url = url[:60] + "..." if len(url) > 60 else url
                print(f"  [爬取 {i}/{len(urls)}] {display_url}", end="", flush=True)
                local_path = self.crawl_page(url, save_dir)
                if local_path:
                    print(" ✓")
                    results.append(local_path)
                else:
                    # 显示失败原因
                    reason = self.last_error or "未知错误"
                    print(f" ✗ ({reason})")
        return results


class HTMLToMarkdown:
    """HTML to Markdown 转换工具"""
    
    @staticmethod
    def convert(html_dir: str, output_file: str, title: str = "搜索结果"):
        """
        将目录中的HTML文件转换为Markdown
        :param html_dir: HTML文件目录
        :param output_file: 输出Markdown文件路径
        :param title: 文档标题
        """
        try:
            import html2text
            from bs4 import BeautifulSoup
            
            # 配置转换器
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            converter.bypass_tables = False
            converter.ignore_images = True
            converter.code_style = 'backticks'
            converter.body_width = 0
            
            all_markdown = f"# {title}\n\n"
            
            # 遍历所有HTML文件
            if not os.path.exists(html_dir):
                return
            
            html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
            
            for filename in sorted(html_files):
                filepath = os.path.join(html_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # 提取主要内容
                    main = (soup.find('main') or 
                           soup.find('article') or 
                           soup.find('div', {'class': 'document'}) or 
                           soup.body)
                    
                    if not main:
                        continue
                    
                    # 移除无关标签
                    for tag in main.find_all(['nav', 'footer', 'script', 'style', 'header']):
                        tag.decompose()
                    
                    # 提取标题
                    page_title = soup.title.string if soup.title else filename
                    page_title = re.sub(r' — .*', '', page_title)
                    
                    # 转换
                    raw_md = converter.handle(str(main))
                    
                    # 标题降级
                    raw_md = re.sub(r'^(#+)\s', r'#\1 ', raw_md, flags=re.MULTILINE)
                    
                    # 清理空白块：移除只有符号、空白行的段落
                    lines = raw_md.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        cleaned_line = line.strip()
                        # 保留：有实际内容、标题行、表格行
                        if cleaned_line and (
                            cleaned_line.startswith('#') or  # 标题
                            cleaned_line.startswith('|') or  # 表格
                            cleaned_line.startswith('-') or  # 列表/hr
                            cleaned_line.startswith('*') or  # 列表
                            cleaned_line.startswith('>') or  # 引用
                            len(cleaned_line) > 5 or  # 有5个以上字符的内容
                            any(c.isalnum() for c in cleaned_line)  # 包含字母数字
                        ):
                            cleaned_lines.append(line)
                    
                    raw_md = '\n'.join(cleaned_lines)
                    
                    all_markdown += f"\n## {page_title}\n\n{raw_md}\n\n---\n\n"
                
                except Exception as e:
                    pass  # 跳过该文件，继续处理其他文件
            
            # 清理连续换行
            all_markdown = re.sub(r'\n{3,}', '\n\n', all_markdown)
            
            # 保存
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(all_markdown)
            
        except ImportError as e:
            print(f"[错误] 缺少依赖库: {e}")


class SearchAugmentedQA:
    """搜索增强的问答工具"""
    
    def __init__(self):
        self.searcher = WebSearcher()
        self.crawler = PageCrawler()
        self.doc_manager = TemporaryDocManager()
    
    def augment_query(self, query: str, num_searches: int = 5) -> Optional[str]:
        """通过Web搜索和RAG增强查询，支持自动换批重试"""
        max_retries = 3
        all_local_files = []
        
        for batch in range(max_retries):
            try:
                # 1. 搜索 - 多次尝试用不同关键词
                if batch == 0:
                    search_query = query
                    print(f"[搜索] 正在搜索: '{query}'")
                else:
                    # 后续批次添加后缀以获取不同结果
                    search_query = query
                    print(f"[搜索] 第 {batch+1} 批搜索...")
                
                search_results = self.searcher.search_duckduckgo(search_query, num_searches)
                
                if not search_results:
                    print(f"[搜索] 搜索无结果")
                    continue
                
                # 2. 爬取 URLs
                urls = [r.get("url") for r in search_results if r.get("url")]
                print(f"[爬取] 准备爬取 {len(urls)} 个页面:")
                for url in urls:
                    print(f"      - {url[:70]}")
                
                html_dir = self.doc_manager.get_html_dir()
                local_files = self.crawler.crawl_pages(urls, html_dir)
                
                if local_files:
                    # 只要有至少1个成功，就停止换批
                    print(f"[爬取] 成功爬取 {len(local_files)}/{len(urls)} 个页面 ✓")
                    all_local_files.extend(local_files)
                    break  # 成功，停止换批
                else:
                    print(f"[爬取] 本批全部失败，尝试换批...")
                    if batch < max_retries - 1:
                        print(f"[爬取] 将尝试第 {batch+2} 批搜索结果...\n")
            
            except Exception as e:
                print(f"[错误] 批次 {batch+1} 异常: {type(e).__name__}")
                continue
        
        # 检查是否有任何页面爬取成功
        if not all_local_files:
            print(f"[爬取] 已尝试 {max_retries} 批，仍无页面可用，返回None")
            return None
        
        # 3. 转换为Markdown
        print(f"[转换] 将HTML转换为Markdown...")
        md_path = self.doc_manager.get_markdown_path()
        HTMLToMarkdown.convert(html_dir, md_path, title=f"搜索结果: {query}")
        
        # 4. RAG检索
        print(f"[RAG] 进行智能上下文检索...")
        augmented_context = self._rag_retrieve(md_path, query)
        return augmented_context
    
    def _rag_retrieve(self, md_path: str, query: str) -> str:
        """
        使用RAG进行上下文检索
        """
        try:
            from storage.rag_retriever import EnhancedMDRAG
            
            rag = EnhancedMDRAG(doc_path=md_path)
            context = rag.search(query)
            print(f"[RAG] 检索成功，获得 {len(context)} 字符的上文")
            return context
        
        except Exception as e:
            print(f"[RAG] 检索失败 ({type(e).__name__})，使用全文")
            # 降级处理：直接读取Markdown文件
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
    
    def cleanup(self):
        """清理临时文件"""
        self.doc_manager.cleanup()
