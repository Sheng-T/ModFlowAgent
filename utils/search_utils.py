"""
Search-augmented Q&A helpers.

Priority order:
  1. Tavily API   — if TAVILY_API_KEY set in api_keys.py (recommended)
  2. SearXNG      — if SEARXNG_URL set in api_keys.py (self-hosted)
  3. Legacy path  — Wikipedia API + DuckDuckGo + page crawling (no config needed)

To use Tavily (free, 1000 req/month):
  1. Sign up at https://app.tavily.com
  2. Copy api_keys.example.py → api_keys.py
  3. Set TAVILY_API_KEY = "tvly-..."
"""
import os
import re
import shutil
from typing import Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from utils.ui_logger import ui_print


# ── Secrets loader ─────────────────────────────────────────────────────────────

def _get_secret(name: str) -> str:
    try:
        import api_keys as _s
        return getattr(_s, name, "") or ""
    except ImportError:
        return ""


# ── Relevance check ────────────────────────────────────────────────────────────

def is_relevant(context: str, query: str) -> bool:
    keywords = [k for k in re.split(r"\W+", query.lower()) if len(k) > 1]
    ctx = context.lower()
    return sum(1 for k in keywords if k in ctx) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# PATH A — Tavily (clean, fast, no crawling)
# ══════════════════════════════════════════════════════════════════════════════

def _tavily_search(query: str, num_results: int = 5) -> Optional[str]:
    """
    Call Tavily API and return a context string ready for the LLM.
    Returns None on failure or if key is not configured.
    """
    api_key = _get_secret("TAVILY_API_KEY")
    if not api_key:
        return None

    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": num_results,
                "include_answer": True,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        blocks: list[str] = []

        # Tavily short answer (when available)
        answer = (data.get("answer") or "").strip()
        if answer:
            blocks.append(f"## Summary\n\n{answer}")

        # Per-result content
        for r in data.get("results", []):
            content = (r.get("content") or "").strip()
            title   = r.get("title", "")
            if content:
                blocks.append(f"## {title}\n\n{content}")

        if not blocks:
            ui_print("  ✗ Tavily: no results")
            return None

        context = "\n\n---\n\n".join(blocks)
        ui_print(f"  ✓ Tavily: {len(blocks)} results, {len(context)} chars")
        return context

    except Exception as e:
        ui_print(f"  ✗ Tavily: {type(e).__name__}: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PATH B — SearXNG public instances (no login, no deployment)
# ══════════════════════════════════════════════════════════════════════════════

_DEFAULT_SEARXNG_INSTANCES = [
    "https://searx.be",
    "https://search.ononoki.org",
    "https://priv.au",
]


def _searxng_search(query: str, num_results: int = 5) -> Optional[str]:
    """Try each SearXNG instance in order; return on first success."""
    # User can override the list in api_keys.py
    # Setting SEARXNG_INSTANCES = [] disables SearXNG entirely
    user_list = _get_secret("SEARXNG_INSTANCES")
    if user_list is None:
        instances = _DEFAULT_SEARXNG_INSTANCES
    elif user_list == []:
        return None
    else:
        instances = user_list

    for base_url in instances:
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/search",
                params={"q": query, "format": "json", "language": "auto"},
                timeout=6,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            results = resp.json().get("results", [])[:num_results]
            blocks  = []
            for r in results:
                snippet = (r.get("content") or r.get("snippet") or "").strip()
                if snippet:
                    blocks.append(f"## {r.get('title', '')}\n\n{snippet}")
            if blocks:
                context = "\n\n---\n\n".join(blocks)
                ui_print(f"  ✓ SearXNG ({base_url}): {len(blocks)} results")
                return context
            ui_print(f"  ✗ SearXNG ({base_url}): no results")
        except Exception as e:
            ui_print(f"  ✗ SearXNG ({base_url}): {type(e).__name__}")

    return None


# ══════════════════════════════════════════════════════════════════════════════
# PATH C — Legacy (Wikipedia + DDG + crawling)
# ══════════════════════════════════════════════════════════════════════════════

BAD_DOMAINS = [
    "doc88.com", "slideserve.com", "wenku.baidu.com", "archive.org",
    "trust.baidu.com", "home.baidu.com", "map.baidu.com",
    "ad.baidu.com", "union.baidu.com", "passport.baidu.com",
]
GOOD_DOMAINS = [
    "baike.baidu.com", "wikipedia.org",
    "ncbi.nlm.nih.gov", "nature.com", "science.org",
]
NON_HTML_EXTENSIONS = (
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.tar', '.gz', '.bz2', '.7z', '.exe', '.bin',
)


def _score_url(url: str) -> int:
    if any(g in url for g in GOOD_DOMAINS): return 2
    if any(b in url for b in BAD_DOMAINS):  return -1
    return 0


def _fetch_wikipedia(query: str) -> Optional[str]:
    for lang in ("zh", "en"):
        try:
            api_url = (
                f"https://{lang}.wikipedia.org/w/api.php"
                f"?action=query&prop=extracts&exintro=1&explaintext=1"
                f"&titles={requests.utils.quote(query)}&format=json&redirects=1"
            )
            resp  = requests.get(api_url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            pages = resp.json().get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if pid == "-1":
                    continue
                extract = page.get("extract", "").strip()
                if extract and len(extract) > 100:
                    ui_print(f"  ✓ Wikipedia ({lang}): {len(extract)} chars")
                    return extract
        except Exception as e:
            ui_print(f"  ✗ Wikipedia ({lang}): {type(e).__name__}")
    return None


def _search_ddg(query: str, num_results: int = 8) -> list[dict]:
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore[import]
        results = []
        for r in DDGS(timeout=5).text(query, max_results=num_results):
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("href") or r.get("url", ""),
                "snippet": r.get("body") or r.get("snippet", ""),
            })
        results.sort(key=lambda x: _score_url(x["url"]), reverse=True)
        if results:
            ui_print(f"  ✓ DuckDuckGo: {len(results)} results")
        return results
    except Exception as e:
        ui_print(f"  ✗ DuckDuckGo: {type(e).__name__}")
        return []


def _search_bing(query: str) -> list[dict]:
    try:
        resp = requests.get(
            f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=zh-CN",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=8,
        )
        soup    = BeautifulSoup(resp.text, "html.parser")
        results = []
        domain_count: dict[str, int] = {}
        for li in soup.select("li.b_algo")[:8]:
            a = li.find("a")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            if any(b in href for b in BAD_DOMAINS):
                continue
            try:
                domain = urlparse(href).netloc
            except Exception:
                domain = href
            if domain_count.get(domain, 0) >= 2:
                continue
            domain_count[domain] = domain_count.get(domain, 0) + 1
            # Bing snippet is in <p> or .b_caption p inside the li
            snippet_tag = li.select_one(".b_caption p, p")
            snippet     = snippet_tag.get_text(strip=True) if snippet_tag else ""
            results.append({"title": a.get_text(strip=True), "url": href, "snippet": snippet})
        if results:
            ui_print(f"  ✓ Bing: {len(results)} results")
        return results
    except Exception as e:
        ui_print(f"  ✗ Bing: {type(e).__name__}")
        return []


def _search_baidu(query: str) -> list[dict]:
    try:
        resp = requests.get(
            f"https://www.baidu.com/s?ie=utf-8&wd={requests.utils.quote(query)}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.baidu.com/",
            },
            timeout=8,
        )
        resp.encoding = "utf-8"
        soup    = BeautifulSoup(resp.text, "html.parser")
        results = []
        for div in soup.select("div.result, div.c-container")[:8]:
            a = div.find("a")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            if href.startswith("/") or href.startswith("#"):
                continue
            if any(b in href for b in BAD_DOMAINS):
                continue
            snippet_tag = div.find("div", class_=re.compile(r"c-abstract|content-right"))
            results.append({
                "title":   a.get_text(strip=True),
                "url":     href,
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
            })
        if results:
            ui_print(f"  ✓ Baidu: {len(results)} results")
        return results
    except Exception as e:
        ui_print(f"  ✗ Baidu: {type(e).__name__}")
        return []


def _search_baike_direct(query: str) -> list[dict]:
    try:
        encoded = requests.utils.quote(query, safe="")
        resp    = requests.get(
            f"https://baike.baidu.com/item/{encoded}",
            headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-CN,zh;q=0.9"},
            timeout=8,
        )
        resp.encoding = "utf-8"
        INDICATORS = ["lemma-summary", "J-summary", "summary-content", "main-content", "para"]
        if resp.status_code == 200 and any(i in resp.text for i in INDICATORS):
            ui_print("  ✓ Baike direct hit")
            return [{"title": query, "url": resp.url, "snippet": ""}]
    except Exception:
        pass
    return []


class _TempDocManager:
    def __init__(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "temp")
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(base, f"session_{ts}")
        os.makedirs(self.session_dir, exist_ok=True)

    def html_dir(self) -> str:
        d = os.path.join(self.session_dir, "html")
        os.makedirs(d, exist_ok=True)
        return d

    def md_path(self) -> str:
        return os.path.join(self.session_dir, "docs.md")

    def cleanup(self):
        try:
            shutil.rmtree(self.session_dir)
        except Exception:
            pass


class _PageCrawler:
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self._ua = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]

    def _session(self):
        import random
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(self._ua),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        return s

    def crawl(self, url: str, save_dir: str) -> Optional[str]:
        clean = url.split("?")[0].split("#")[0].lower()
        if clean.endswith(NON_HTML_EXTENSIONS):
            return None
        try:
            resp = self._session().get(url, timeout=self.timeout, allow_redirects=True)
            resp.encoding = "utf-8"
            if "text/html" not in resp.headers.get("Content-Type", ""):
                return None
            fname = (urlparse(url).netloc + urlparse(url).path).replace("/", "_").strip("_")[:80] + ".html"
            path  = os.path.join(save_dir, fname)
            os.makedirs(save_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            return path
        except Exception:
            return None

    def crawl_many(self, urls: list[str], save_dir: str) -> list[str]:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        valid = [u for u in urls if not u.split("?")[0].lower().endswith(NON_HTML_EXTENSIONS)]
        if not valid:
            return []
        ui_print(f"  [crawl] {len(valid)} pages (timeout={self.timeout}s)")
        results, futures = [], {}
        with ThreadPoolExecutor(max_workers=min(len(valid), 5)) as ex:
            for u in valid:
                futures[ex.submit(self.crawl, u, save_dir)] = u
            for fut in as_completed(futures):
                u   = futures[fut]
                tag = u[:60] + "..." if len(u) > 60 else u
                try:
                    path = fut.result()
                    if path:
                        ui_print(f"  ✓ {tag}")
                        results.append(path)
                    else:
                        ui_print(f"  ✗ {tag}")
                except Exception:
                    ui_print(f"  ✗ {tag}")
        return results


def _html_dir_to_md(html_dir: str, md_path: str, query: str) -> None:
    try:
        import html2text
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.body_width = 0

        parts = [f"# Search results: {query}\n"]
        for fname in sorted(os.listdir(html_dir)):
            if not fname.endswith(".html"):
                continue
            try:
                with open(os.path.join(html_dir, fname), encoding="utf-8") as f:
                    html = f.read()
                soup  = BeautifulSoup(html, "html.parser")
                main  = soup.find("main") or soup.find("article") or soup.body
                if not main:
                    continue
                for tag in main.find_all(["nav", "footer", "script", "style", "header"]):
                    tag.decompose()
                title = (soup.title.string or fname) if soup.title else fname
                title = re.sub(r" [—-].*", "", title)
                md    = converter.handle(str(main))
                md    = re.sub(r"\n{3,}", "\n\n", md)
                parts.append(f"\n## {title}\n\n{md}\n\n---\n")
            except Exception:
                pass
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
    except ImportError:
        pass


def _rag_retrieve(md_path: str, query: str) -> str:
    try:
        from storage.rag_retriever import EnhancedMDRAG
        vec_cache = os.path.join(os.path.dirname(md_path), "vec_cache")
        rag = EnhancedMDRAG(doc_path=md_path, cache_dir=vec_cache)
        return rag.search(query)
    except Exception:
        try:
            with open(md_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""


def _legacy_augment(query: str, num_searches: int = 5) -> Optional[str]:
    """Bing + Baidu + DDG snippets → crawling → Wikipedia fallback."""
    doc_mgr       = _TempDocManager()
    crawler       = _PageCrawler()
    snippet_texts: list[str] = []
    all_files:    list[str] = []

    try:
        # 1. Bing snippets (fast, broad coverage, no crawling yet)
        ui_print("[Search] Bing...")
        bing_results = _search_bing(query)
        for r in bing_results:
            if r.get("snippet"):
                snippet_texts.append(f"## {r['title']}\n\n{r['snippet']}")

        # 2. Baidu snippets + baike direct
        ui_print("[Search] Baidu + Baike...")
        search_results = _search_baike_direct(query)
        baidu = _search_baidu(query)
        for r in baidu:
            if r.get("snippet"):
                snippet_texts.append(f"## {r['title']}\n\n{r['snippet']}")
        search_results.extend(baidu)
        search_results.extend(bing_results)

        # 3. If snippets already rich enough, skip crawling
        combined_snippets = "\n\n---\n\n".join(snippet_texts)
        if len(combined_snippets) >= 600 and is_relevant(combined_snippets, query):
            ui_print("[Search] Snippets sufficient — skipping crawling")
            return combined_snippets

        # 4. Crawl collected URLs
        if search_results:
            urls  = [r["url"] for r in search_results if r.get("url")]
            files = crawler.crawl_many(urls, doc_mgr.html_dir())
            all_files.extend(files)

        # 5. DDG supplement if still short
        if len(all_files) < 2:
            ui_print("[Search] DuckDuckGo...")
            BLACKLIST = ["wenku", "doc88", "slideserve", "archive.org",
                         "csdn.net", "taobao", "jd.com", "amazon"]
            WHITELIST = ["baike.baidu.com", "wikipedia.org",
                         "ncbi.nlm.nih.gov", "nature.com", "science.org"]
            ddg = _search_ddg(query, num_searches)
            extra_urls = []
            for r in ddg:
                url = r.get("url", "")
                if any(b in url for b in BLACKLIST):
                    continue
                if r.get("snippet"):
                    snippet_texts.append(f"## {r['title']}\n\n{r['snippet']}")
                if any(g in url for g in WHITELIST):
                    extra_urls.insert(0, url)
                else:
                    extra_urls.append(url)
            if extra_urls:
                files = crawler.crawl_many(extra_urls[:3], doc_mgr.html_dir())
                all_files.extend(files)

        # 6. Wikipedia as last-resort supplement (concept definitions)
        if not snippet_texts and not all_files:
            ui_print("[Search] Wikipedia (last resort)...")
            wiki = _fetch_wikipedia(query)
            if wiki:
                snippet_texts.append(f"## Wikipedia: {query}\n\n{wiki}")

        # 6. HTML → MD → RAG
        context = None
        if all_files:
            ui_print("[Search] Converting HTML → context...")
            _html_dir_to_md(doc_mgr.html_dir(), doc_mgr.md_path(), query)
            context = _rag_retrieve(doc_mgr.md_path(), query)

        # 7. Snippet fallback
        if (not context or len(context.strip()) < 300) and snippet_texts:
            ui_print(f"[Search] Using {len(snippet_texts)} snippets as fallback")
            context = "\n\n---\n\n".join(snippet_texts)

        if not context or len(context.strip()) < 100:
            return None
        if not is_relevant(context, query):
            ui_print("[Search] Context not relevant — discarding")
            return None

        return context

    finally:
        doc_mgr.cleanup()


# ══════════════════════════════════════════════════════════════════════════════
# Public interface
# ══════════════════════════════════════════════════════════════════════════════

class SearchAugmentedQA:
    """
    Unified search wrapper.  Tries Tavily → SearXNG → legacy crawling.
    Configure keys in api_keys.py (gitignored).
    """

    def augment_query(self, query: str, num_searches: int = 5) -> Optional[str]:
        # Path A: Tavily
        tavily_key = _get_secret("TAVILY_API_KEY")
        if tavily_key:
            ui_print("[Search] Using Tavily...")
            result = _tavily_search(query, num_searches)
            if result:
                return result
            ui_print("[Search] Tavily failed — falling back to legacy")

        # Path B: SearXNG
        searxng_url = _get_secret("SEARXNG_URL")
        if searxng_url:
            ui_print("[Search] Using SearXNG...")
            result = _searxng_search(query, num_searches)
            if result:
                return result
            ui_print("[Search] SearXNG failed — falling back to legacy")

        # Path C: legacy
        ui_print("[Search] Using legacy (Wikipedia + DDG + crawling)...")
        return _legacy_augment(query, num_searches)

    def cleanup(self):
        pass  # legacy path cleans up in its own finally block
