"""Web搜索和RAG增强工具 - 用于answer_general_question_node"""
import os
import re
import shutil
from typing import List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# 多层级导入保证兼容性
try:
    from utils.ui_logger import ui_print
except ImportError:
    try:
        # 同目录的相对导入
        from .ui_logger import ui_print
    except ImportError:
        # 降级：没有 ui_logger 就用普通 print
        ui_print = print

BAD_DOMAINS = [
    "doc88.com",
    "slideserve.com",
    "wenku.baidu.com",
    "archive.org",
]

GOOD_DOMAINS = [
    "baike.baidu.com",
    "wikipedia.org",
    "ncbi.nlm.nih.gov",
    "nature.com",
    "science.org",
]


# 在 WebSearcher 类里加这个方法

def is_relevant(context: str, query: str) -> bool:
    """
    简单关键词相关性判断（轻量级，够用）
    """
    if not context:
        return False

    query = query.lower()
    context = context.lower()

    # 拆词（简单版本）
    keywords = [k for k in re.split(r"\W+", query) if len(k) > 1]

    match_count = sum(1 for k in keywords if k in context)

    # 至少命中1个关键词
    return match_count >= 1

def score_url(url):
    if any(g in url for g in GOOD_DOMAINS):
        return 2
    if any(b in url for b in BAD_DOMAINS):
        return -1
    return 0

def search_bing(query):
    url = f"https://www.bing.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    resp = requests.get(url, headers=headers, timeout=8)
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    domain_count = {}  # 记录每个域名出现次数

    for li in soup.select("li.b_algo"):
        if len(results) >= 5:
            break
        a = li.find("a")
        if not a or "href" not in a.attrs:
            continue
        href = a["href"]
        if any(b in href for b in BAD_DOMAINS):
            continue

        # 提取主域名
        try:
            domain = urlparse(href).netloc  # 例如 "www.zhihu.com"
        except Exception:
            domain = href

        # 每个域名最多保留 2 个
        if domain_count.get(domain, 0) >= 2:
            continue

        domain_count[domain] = domain_count.get(domain, 0) + 1
        results.append({
            "title": a.get_text(strip=True),
            "url": href,
            "snippet": ""
        })

    return results


def search_baidu(query):
    url = f"https://www.baidu.com/s?ie=utf-8&wd={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    resp = requests.get(url, headers=headers, timeout=8)
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    # 百度的结果块是 div.result，不是 li.b_algo
    for div in soup.select("div.result")[:5]:
        a = div.find("a")
        if a and "href" in a.attrs:
            results.append({
                "title": a.get_text(strip=True),
                "url": a["href"],
                "snippet": ""
            })
    return results

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
                ui_print(f"[清理] 临时文件清理失败: {e}")


class WebSearcher:
    """Web搜索工具"""
    
    @staticmethod
    def search_duckduckgo(query: str, num_results: int = 8) -> List[dict]:
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
                    ui_print("  [警告] 检测到旧库 duckduckgo_search，建议升级: pip install ddgs")
                except ImportError:
                    ui_print("\n【提示】搜索库未安装，请运行:")
                    ui_print("  python utils/check_dependencies.py")
                    ui_print("\n或手动安装:")
                    ui_print("  pip install ddgs html2text beautifulsoup4")
                    ui_print("\n不安装搜索库也可使用纯LLM回答。\n")
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

                results.sort(key=lambda x: score_url(x["url"]), reverse=True)
                if results:
                    ui_print(f"  ✓ 搜索成功: 找到 {len(results)} 个结果")
                else:
                    ui_print(f"  ✗ 搜索无结果")
                    
            except Exception as inner_e:
                ui_print(f"  ✗ 搜索网络异常: {type(inner_e).__name__}")
            
            return results
            
        except Exception as e:
            ui_print(f"  ✗ 搜索失败: {type(e).__name__}")
            return []
    
    @staticmethod
    def search_google_simple(query: str, num_results: int = 5) -> List[dict]:
        """
        简单的Google搜索备选方案（通过googlesearch库）
        """
        return []  # 当前不支持Google搜索，使用DuckDuckGo


# 需要忽略的非HTML资源扩展名
NON_HTML_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.tar', '.gz', '.bz2', '.7z', '.exe', '.bin')


class PageCrawler:
    """页面爬取工具"""
    
    def __init__(self, timeout: int = 20, max_retries: int = 3):
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
                # 过滤非HTML资源，避免下载PDF等二进制文件
                clean_url = url.split('?', 1)[0].split('#', 1)[0].lower()
                if clean_url.endswith(NON_HTML_EXTENSIONS):
                    self.last_error = f"跳过非HTML资源: {clean_url}"
                    return None

                # 随机延迟 0.5-1.5 秒，模拟人工浏览
                time.sleep(random.uniform(0.5, 1.5))
                
                # 轮换 User-Agent
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.encoding = 'utf-8'
                response.raise_for_status()

                # 仅保存HTML页面，过滤二进制/非HTML类型（例如 PDF）
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                    self.last_error = f"非HTML类型，跳过: {content_type}"
                    return None

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
            if not url:
                continue

            clean_url = url.split('?', 1)[0].split('#', 1)[0].lower()
            if clean_url.endswith(NON_HTML_EXTENSIONS):
                ui_print(f"  [跳过 非HTML资源 {i}/{len(urls)}] {clean_url}")
                continue

            display_url = url[:60] + "..." if len(url) > 60 else url
            ui_print(f"  [爬取 {i}/{len(urls)}] {display_url}", end="", flush=True)
            local_path = self.crawl_page(url, save_dir)
            if local_path:
                ui_print(" ✓")
                results.append(local_path)
            else:
                # 显示失败原因
                reason = self.last_error or "未知错误"
                ui_print(f" ✗ ({reason})")
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
            ui_print(f"[错误] 缺少依赖库: {e}")


class SearchAugmentedQA:
    """搜索增强的问答工具"""
    
    def __init__(self):
        self.searcher = WebSearcher()
        self.crawler = PageCrawler()
        self.doc_manager = TemporaryDocManager()

    @staticmethod
    def search_baike_direct(query: str, num_results: int = 3) -> List[dict]:
        """
        直接搜索百度百科和维基百科，不经过DDG
        """
        results = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })

        # 1. 百度百科直接搜索
        try:
            url = f"https://baike.baidu.com/item/{requests.utils.quote(query)}"
            resp = session.get(url, timeout=5)

            if resp.status_code == 200 and "lemma-summary" in resp.text:
                results.append({
                    "title": query,
                    "url": url,
                    "snippet": "百度百科词条"
                })
                ui_print("  ✓ 百度百科直达成功")
            else:
                ui_print("  ✗ 百度百科未命中")

        except Exception as e:
            ui_print(f"  ✗ 百度百科失败: {type(e).__name__}")

        # 2. 中文维基百科
        try:
            wiki_url = f"https://zh.wikipedia.org/wiki/{requests.utils.quote(query)}"
            resp = session.get(wiki_url, timeout=8)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 直接命中词条时页面就是词条本身
            if '/wiki/' in resp.url and 'search' not in resp.url:
                results.append({
                    "title": soup.find('h1').get_text() if soup.find('h1') else query,
                    "url": resp.url,
                    "snippet": ""
                })
                ui_print(f"  ✓ 维基百科: 直接命中词条")
            else:
                # 搜索结果页，找第一个词条
                for a in soup.select('.mw-search-result-heading a'):
                    full_url = urljoin('https://zh.wikipedia.org', a['href'])
                    results.append({
                        "title": a.get_text(strip=True),
                        "url": full_url,
                        "snippet": ""
                    })
                    break
                if any('wikipedia' in r['url'] for r in results):
                    ui_print(f"  ✓ 维基百科: 找到搜索结果")
        except Exception as e:
            ui_print(f"  ✗ 维基百科搜索失败: {type(e).__name__}")

        return results

    def augment_query(self, query: str, num_searches: int = 5) -> Optional[str]:

        all_local_files = []
        html_dir = self.doc_manager.get_html_dir()

        # ===== 第1步：优先直接搜百科（最可靠）=====
        ui_print(f"[Search] 优先搜索百科...")
        search_results = []

        baike_results = self.search_baike_direct(query, num_results=2)

        # 先百科
        if baike_results:
            search_results.extend(baike_results)

        if len(search_results) < 2:
            ui_print("[Search] 使用Baidu补充...")
            try:
                bing_results = search_baidu(query)
                search_results.extend(bing_results)
            except Exception as e:
                ui_print(f"[Search] Bing失败: {type(e).__name__}")

        # 不够 → Bing补充
        if len(search_results) < 2:
            ui_print("[Search] 使用Bing补充...")
            try:
                bing_results = search_bing(query)
                search_results.extend(bing_results)
            except Exception as e:
                ui_print(f"[Search] Bing失败: {type(e).__name__}")

        if search_results:
            urls_to_crawl = [r['url'] for r in search_results]
            ui_print(f"[爬取] 准备爬取百科/Bing的 {len(urls_to_crawl)} 个页面")
            local_files = self.crawler.crawl_pages(urls_to_crawl, html_dir)
            all_local_files.extend(local_files)

        # ===== 第3步：如果百科结果不够，用DDG补充（严格过滤）=====
        if len(all_local_files) < 2:
            ui_print(f"[Search] 百科不够，使用DDG补充...")

            # 严格过滤：只保留可信域名
            STRICT_WHITELIST = [
                "baike.baidu.com",
                "zh.wikipedia.org",
                "wikipedia.org",
                "ncbi.nlm.nih.gov",
                "nature.com",
                "science.org",
                "zhihu.com/p",  # 知乎文章（非问答页）
                "mp.weixin.qq.com",  # 微信公众号
            ]

            # 严格黑名单（直接丢弃）
            STRICT_BLACKLIST = [
                "aiqicha", "wenku", "doc88", "slideserve",
                "archive.org", "csdn.net", "douban.com",
                "taobao", "jd.com", "amazon", "shop",
            ]

            ddg_results = self.searcher.search_duckduckgo(query, num_searches)

            filtered_urls = []
            for r in ddg_results:
                url = r.get("url", "")
                # 黑名单直接跳过
                if any(bad in url for bad in STRICT_BLACKLIST):
                    ui_print(f"  [过滤] 黑名单跳过: {url[:50]}")
                    continue
                # 优先白名单
                if any(good in url for good in STRICT_WHITELIST):
                    filtered_urls.insert(0, url)  # 放前面优先爬
                else:
                    filtered_urls.append(url)

            # 最多补充3个
            filtered_urls = filtered_urls[:3]
            if filtered_urls:
                ui_print(f"[读取] DDG补充 {len(filtered_urls)} 个页面")
                local_files = self.crawler.crawl_pages(filtered_urls, html_dir)
                all_local_files.extend(local_files)

        # ===== 后续RAG流程不变 =====
        if not all_local_files:
            ui_print(f"[Search] 所有来源均失败，降级纯 LLM")
            return None

        ui_print(f"[转换] 将HTML转换为Markdown...")
        md_path = self.doc_manager.get_markdown_path()
        HTMLToMarkdown.convert(html_dir, md_path, title=f"搜索结果: {query}")

        ui_print(f"[RAG] 进行普適上下文检索...")
        augmented_context = self._rag_retrieve(md_path, query)

        if not augmented_context or len(augmented_context.strip()) < 300:
            ui_print(f"[RAG] 结果过短，降级为纯LLM（长度 {len(augmented_context or '')})）")
            return None
        if not is_relevant(augmented_context, query):
            ui_print("[RAG] 内容与 query 不相关，丢弃")
            return None

        return augmented_context
    
    def _rag_retrieve(self, md_path: str, query: str) -> str:
        """
        使用RAG进行上下文检索
        """
        try:
            from storage.rag_retriever import EnhancedMDRAG
            
            rag = EnhancedMDRAG(doc_path=md_path)
            context = rag.search(query)
            ui_print(f"[RAG] 检索成功，获得 {len(context)} 字符的上文")
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
