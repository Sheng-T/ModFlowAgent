"""Web搜索和RAG增强工具 - 用于answer_general_question_node"""
import os
import re
import shutil
from typing import List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# 统一使用顶级 `utils.ui_logger` 导出
from utils.ui_logger import ui_print

BAD_DOMAINS = [
    "doc88.com",
    "slideserve.com",
    "wenku.baidu.com",
    "archive.org",
    # Baidu 内部服务页（认证、地图、广告等），内容与搜索词无关
    "trust.baidu.com",
    "home.baidu.com",
    "map.baidu.com",
    "ad.baidu.com",
    "union.baidu.com",
    "passport.baidu.com",
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
        if len(results) >= 10:
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.baidu.com/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = "utf-8"
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    # 百度结果块选择器（兼容多版本布局）
    for div in soup.select("div.result, div.c-container")[:6]:
        a = div.find("a")
        if not a or "href" not in a.attrs:
            continue
        href = a["href"]
        # 相对路径 → 跳过（/s?wd=... 这类是百度内部搜索链接，没有实际内容）
        if href.startswith("/") or href.startswith("#"):
            continue
        if any(b in href for b in BAD_DOMAINS):
            continue
        # 提取摘要文字
        snippet_tag = div.find("div", class_=re.compile(r"c-abstract|content-right"))
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        results.append({
            "title": a.get_text(strip=True),
            "url": href,
            "snippet": snippet
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

    # 每个 URL 只试一次，失败就跳过（重试意义不大，只是浪费时间）
    def __init__(self, timeout: int = 8, max_retries: int = 1):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def _make_session(self) -> requests.Session:
        import random
        s = requests.Session()
        s.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return s

    def crawl_page(self, url: str, save_dir: str) -> tuple[Optional[str], str]:
        """
        爬取单个页面。返回 (本地路径 or None, 错误信息)
        """
        from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

        clean_url = url.split('?', 1)[0].split('#', 1)[0].lower()
        if clean_url.endswith(NON_HTML_EXTENSIONS):
            return None, "非HTML资源"

        session = self._make_session()
        for _ in range(self.max_retries):
            try:
                response = session.get(url, timeout=self.timeout, allow_redirects=True)
                response.encoding = 'utf-8'
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                    return None, f"非HTML({content_type[:20]})"

                parsed = urlparse(url)
                filename = (parsed.netloc + parsed.path).replace('/', '_').strip('_') or 'index'
                if not filename.endswith('.html'):
                    filename += '.html'
                filename = filename[:80]  # 防止文件名过长

                os.makedirs(save_dir, exist_ok=True)
                local_path = os.path.join(save_dir, filename)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return local_path, ""

            except Timeout:
                return None, "超时"
            except ConnectionError:
                return None, "连接失败"
            except HTTPError as e:
                return None, f"HTTP{e.response.status_code}"
            except RequestException as e:
                return None, type(e).__name__
            except Exception as e:
                return None, type(e).__name__

        return None, "未知错误"

    def crawl_pages(self, urls: List[str], save_dir: str) -> List[str]:
        """
        并行爬取页面（ThreadPoolExecutor），大幅缩短总耗时
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        valid_urls = [
            u for u in urls
            if u and not u.split('?', 1)[0].split('#', 1)[0].lower().endswith(NON_HTML_EXTENSIONS)
        ]
        if not valid_urls:
            return []

        ui_print(f"  [并行爬取] {len(valid_urls)} 个页面 (超时={self.timeout}s)")

        results = []
        futures = {}
        with ThreadPoolExecutor(max_workers=min(len(valid_urls), 5)) as executor:
            for url in valid_urls:
                futures[executor.submit(self.crawl_page, url, save_dir)] = url
 
            for future in as_completed(futures):
                url = futures[future]
                display = url[:80] + "..." if len(url) > 80 else url
                try:
                    local_path, err = future.result()
                    if local_path:
                        ui_print(f"  ✓ {display}")
                        results.append(local_path)
                    else:
                        ui_print(f"  ✗ {display} ({err})")
                except Exception as e:
                    ui_print(f"  ✗ {display} ({type(e).__name__})")

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
    def fetch_wikipedia_api(query: str) -> Optional[str]:
        """
        使用 Wikipedia REST API 直接获取词条纯文本（不需要爬页面）
        优先中文，失败时尝试英文
        返回: 纯文本摘要，失败返回 None
        """
        for lang in ("zh", "en"):
            try:
                # Wikipedia REST API — 返回 JSON，含纯文本摘要
                api_url = (
                    f"https://{lang}.wikipedia.org/w/api.php"
                    f"?action=query&prop=extracts&exintro=1&explaintext=1"
                    f"&titles={requests.utils.quote(query)}&format=json&redirects=1"
                )
                resp = requests.get(api_url, timeout=6,
                                    headers={"User-Agent": "Mozilla/5.0"})
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page in pages.items():
                    if page_id == "-1":
                        continue
                    extract = page.get("extract", "").strip()
                    if extract and len(extract) > 100:
                        ui_print(f"  ✓ Wikipedia API ({lang}): 获得 {len(extract)} 字")
                        return extract
            except Exception as e:
                ui_print(f"  ✗ Wikipedia API ({lang}) 失败: {type(e).__name__}")
        return None

    @staticmethod
    def search_baike_direct(query: str) -> List[dict]:
        """
        直接搜索百度百科，不经过DDG
        """
        results = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.baidu.com/',
        })

        # 百度百科直接搜索
        try:
            encoded = requests.utils.quote(query, safe='')
            url = f"https://baike.baidu.com/item/{encoded}"
            resp = session.get(url, timeout=8)
            resp.encoding = "utf-8"

            # 百度百科多版本布局兼容（class 名会随版本变化）
            BAIKE_INDICATORS = [
                "lemma-summary", "J-summary", "summary-content",
                "main-content", "lemmaSummary", "basicInfo",
                "para", "description"
            ]
            hit = resp.status_code == 200 and any(
                ind in resp.text for ind in BAIKE_INDICATORS
            )
            if hit:
                results.append({
                    "title": query,
                    "url": resp.url,  # 跟随重定向后的真实 URL
                    "snippet": "百度百科词条"
                })
                ui_print("  ✓ 百度百科直达成功")
            else:
                # 搜索接口兜底
                search_url = f"https://baike.baidu.com/search/word?word={encoded}"
                resp2 = session.get(search_url, timeout=5)
                soup2 = BeautifulSoup(resp2.text, "html.parser")
                first = soup2.select_one("dl.search-list dt a, .result-title a")
                if first and first.get("href"):
                    full_url = urljoin("https://baike.baidu.com", first["href"])
                    results.append({"title": first.get_text(strip=True), "url": full_url, "snippet": ""})
                    ui_print(f"  ✓ 百度百科搜索命中: {first.get_text(strip=True)[:30]}")
                else:
                    ui_print("  ✗ 百度百科未命中")

        except Exception as e:
            ui_print(f"  ✗ 百度百科失败: {type(e).__name__}")

        return results

    def augment_query(self, query: str, num_searches: int = 5) -> Optional[str]:

        all_local_files = []
        snippet_texts = []   # 搜索结果的 snippet，爬取失败时作为兜底
        html_dir = self.doc_manager.get_html_dir()

        # ===== 第1步：Wikipedia API（纯文本，不需要爬页面）=====
        ui_print(f"[Search] 尝试 Wikipedia API...")
        wiki_text = self.fetch_wikipedia_api(query)
        if wiki_text:
            snippet_texts.append(f"## Wikipedia: {query}\n\n{wiki_text}")
            # Wikipedia 已经足够详细，直接跳过后续爬取
            if len(wiki_text) >= 500 and is_relevant(wiki_text, query):
                ui_print(f"[Search] Wikipedia 内容充足，跳过爬取")
                return wiki_text

        # ===== 第2步：百度百科直达 =====
        ui_print(f"[Search] 搜索百度百科...")
        search_results = []
        baike_results = self.search_baike_direct(query)
        if baike_results:
            search_results.extend(baike_results)

        # ===== 第3步：Baidu 搜索补充 =====
        if len(search_results) < 2:
            ui_print("[Search] 使用Baidu补充...")
            try:
                baidu_results = search_baidu(query)
                # 收集 snippet（即使页面爬不到也有用）
                for r in baidu_results:
                    if r.get("snippet"):
                        snippet_texts.append(
                            f"## {r['title']}\n\n{r['snippet']}"
                        )
                search_results.extend(baidu_results)
            except Exception as e:
                ui_print(f"[Search] Baidu失败: {type(e).__name__}")

        # ===== 第4步：爬取百科/Baidu 页面 =====
        if search_results:
            urls_to_crawl = [r['url'] for r in search_results]
            ui_print(f"[爬取] 准备爬取 {len(urls_to_crawl)} 个页面")
            local_files = self.crawler.crawl_pages(urls_to_crawl, html_dir)
            all_local_files.extend(local_files)

        # ===== 第5步：如果爬取不够，DDG 补充（严格过滤）=====
        if len(all_local_files) < 2:
            ui_print(f"[Search] 爬取不足，使用DDG补充...")

            STRICT_WHITELIST = [
                "baike.baidu.com", "zh.wikipedia.org", "wikipedia.org",
                "ncbi.nlm.nih.gov", "nature.com", "science.org",
                "zhihu.com/p", "mp.weixin.qq.com",
            ]
            STRICT_BLACKLIST = [
                "aiqicha", "wenku", "doc88", "slideserve",
                "archive.org", "csdn.net", "douban.com",
                "taobao", "jd.com", "amazon", "shop",
            ]

            ddg_results = self.searcher.search_duckduckgo(query, num_searches)

            filtered_urls = []
            for r in ddg_results:
                url = r.get("url", "")
                if any(bad in url for bad in STRICT_BLACKLIST):
                    continue
                # DDG snippet 直接收集，不依赖爬取成功
                if r.get("snippet"):
                    snippet_texts.append(f"## {r.get('title','')}\n\n{r['snippet']}")
                if any(good in url for good in STRICT_WHITELIST):
                    filtered_urls.insert(0, url)
                else:
                    filtered_urls.append(url)

            filtered_urls = filtered_urls[:3]
            if filtered_urls:
                ui_print(f"[爬取] DDG补充 {len(filtered_urls)} 个页面")
                local_files = self.crawler.crawl_pages(filtered_urls, html_dir)
                all_local_files.extend(local_files)

        # ===== 第6步：HTML → Markdown → RAG =====
        augmented_context = None
        if all_local_files:
            ui_print(f"[转换] 将HTML转换为Markdown...")
            md_path = self.doc_manager.get_markdown_path()
            HTMLToMarkdown.convert(html_dir, md_path, title=f"搜索结果: {query}")
            ui_print(f"[RAG] 进行上下文检索...")
            augmented_context = self._rag_retrieve(md_path, query)

        # ===== 第7步：爬取结果不足时，用 snippet 兜底 =====
        if (not augmented_context or len(augmented_context.strip()) < 300) and snippet_texts:
            ui_print(f"[Fallback] 爬取结果不足，使用 {len(snippet_texts)} 条 snippet 作为上下文")
            augmented_context = "\n\n---\n\n".join(snippet_texts)

        if not augmented_context or len(augmented_context.strip()) < 100:
            ui_print(f"[Search] 所有来源均失败，降级纯 LLM")
            return None

        if not is_relevant(augmented_context, query):
            ui_print("[RAG] 内容与 query 不相关，丢弃")
            return None

        return augmented_context
    
    def _rag_retrieve(self, md_path: str, query: str) -> str:
        """
        使用RAG进行上下文检索。
        cache_dir 传入 md_path 同级的 vec_cache/ 子目录，
        确保每次搜索都使用本次爬取的内容，不复用工具文档数据库。
        """
        try:
            from storage.rag_retriever import EnhancedMDRAG

            # 每次搜索都用独立的临时向量缓存目录，避免命中旧工具文档 DB
            vec_cache = os.path.join(os.path.dirname(md_path), "vec_cache")

            rag = EnhancedMDRAG(doc_path=md_path, cache_dir=vec_cache)
            context = rag.search(query)
            ui_print(f"[RAG] 检索成功，获得 {len(context)} 字符的上文")
            return context

        except Exception as e:
            print(f"[RAG] 检索失败 ({type(e).__name__})，使用全文")
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
    
    def cleanup(self):
        """清理临时文件"""
        self.doc_manager.cleanup()
