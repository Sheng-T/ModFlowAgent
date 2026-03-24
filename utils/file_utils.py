import os
import re
from bs4 import BeautifulSoup
import html2text
import os
import requests
from urllib.parse import urljoin, urlparse
import time

def setup_converter():
    """配置 HTML 转 Markdown 的参数"""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.bypass_tables = False  # 重要：保留表格结构
    converter.ignore_images = True  # 生信文档图片多为装饰，可忽略以省 Token
    converter.code_style = 'backticks'  # 使用 ``` 包围代码
    converter.body_width = 0  # 不限制换行，方便 LLM 阅读
    return converter


def clean_html_and_convert(file_path, converter):
    """清洗 HTML 并提取核心内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # --- 去噪策略 ---
    # 针对常见的 ReadTheDocs 或官网结构，只保留 main, article 或特定 ID 的内容
    main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', {'class': 'document'}) or
            soup.find('div', {'id': 'content'}) or
            soup.body
    )

    if not main_content:
        return ""

    # 剔除常见的无关元素
    for tag in main_content.find_all(['nav', 'footer', 'script', 'style', 'header']):
        tag.decompose()

    # 获取文章标题，作为 Markdown 的二级标题
    title = soup.title.string if soup.title else os.path.basename(file_path)
    title = re.sub(r' — .*', '', title)

    raw_md = converter.handle(str(main_content))

    # 核心修复：将内容中的所有标题整体降级！
    # # 变成 ##, ## 变成 ###，以此类推
    raw_md = re.sub(r'^(#+)\s', r'#\1 ', raw_md, flags=re.MULTILINE)

    # 现在的 title 是唯一的一级标题
    markdown_text = f"\n\n# 工具文档: {title}\n\n"
    markdown_text += raw_md

    return markdown_text


def html2md(input_dir, output_file, title):
    converter = setup_converter()
    all_markdown = f"# {title}\n"

    print(f"开始递归处理目录: {input_dir}")

    # 使用 os.walk 递归遍历所有子文件夹
    file_list = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.endswith('.html'):
                # 记录完整路径
                file_list.append(os.path.join(root, f))

    # 排序以保证合并顺序的一致性
    file_list.sort()
    print(f"共发现 {len(file_list)} 个 HTML 文件")

    for file_path in file_list:
        print(f"正在解析: {os.path.basename(file_path)}...")
        try:
            md_content = clean_html_and_convert(file_path, converter)
            all_markdown += md_content
        except Exception as e:
            print(f"错误: 无法处理 {file_path} - {str(e)}")

    # 最后的简单清洗
    all_markdown = re.sub(r'\n{3,}', '\n\n', all_markdown)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(all_markdown)

    print(f"\n处理完成，Markdown 已保存至: {output_file}")


# START_URL = "https://software-docs.nanoporetech.com/dorado/latest/"
# SAVE_DIR = "dorado_docs_html"
# 只爬取该域名下的子路径，防止爬到互联网其他地方去

def crawl_docs(start_url, save_dir, max_depth=5):
    """
    递归爬虫：支持按目录前缀爬取子网页
    :param start_url: 文档起始地址
    :param save_dir: 本地存储绝对路径
    :param max_depth: 最大爬取深度，防止陷入循环
    """
    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc
    # 获取起始 URL 的所在目录，作为匹配前缀
    base_dir = os.path.dirname(parsed_start.path)
    if not base_dir.endswith('/'):
        base_dir += '/'

    visited_urls = set()

    def _recursive_download(current_url, depth):
        if current_url in visited_urls or depth > max_depth:
            return

        try:
            time.sleep(0.3)  # 礼貌爬取
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            visited_urls.add(current_url)

            # --- 映射本地路径 ---
            parsed_current = urlparse(current_url)
            # 获取相对目录结构，避免文件名冲突
            rel_path = parsed_current.path.replace(os.path.dirname(base_dir), "").strip("/")
            if not rel_path or rel_path == "":
                local_file_path = os.path.join(save_dir, "index.html")
            else:
                # 确保保存的路径包含后缀
                local_file_path = os.path.join(save_dir,
                                               f"{rel_path}" if rel_path.endswith('.html') else f"{rel_path}.html")

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            with open(local_file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"[SUCCESS] Depth {depth} | {current_url}")

            # --- 寻找子链接 ---
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href']).split('#')[0].rstrip('/')

                # 过滤规则：
                # 1. 域名一致 2. 路径以 base_dir 开头 3. 排除常见二进制文件
                parsed_full = urlparse(full_url)
                if (parsed_full.netloc == base_domain and
                        parsed_full.path.startswith(base_dir) and
                        not full_url.lower().endswith(('.pdf', '.zip', '.bam', '.gz')) and
                        full_url not in visited_urls):
                    _recursive_download(full_url, depth + 1)

        except Exception as e:
            print(f"[ERROR] Failed to crawl {current_url}: {e}")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f">> start job: {start_url} -> {save_dir}")
    _recursive_download(start_url, 0)
    print(f">> job finish! total {len(visited_urls)} pages.")


if __name__ == "__main__":
    # https://software-docs.nanoporetech.com/dorado/latest/

    # target_url = "https://www.htslib.org/doc/samtools.html"
    # target_dir = "/home/buguai/project/agent/static/samtools/html"
    #
    # crawl_docs(target_url, target_dir)

    html2md(
        input_dir="/home/buguai/project/agent/static/samtools/html",
        output_file="/home/buguai/project/agent/static/samtools/samtools_doc.md",
        title="Samtools Document"
    )