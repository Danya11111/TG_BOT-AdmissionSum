import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import time
from collections import deque
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup


ALLOWED_DOMAINS = {"guu.ru", "priem.guu.ru"}
SEEDS = ["https://guu.ru/", "https://priem.guu.ru/"]

RAW_DIR = os.path.join("data", "guu", "raw")
CHUNKS_DIR = os.path.join("data", "guu", "chunks")
INDEX_PATH = os.path.join("data", "guu", "index.json")


def ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)


def is_allowed_url(url: str) -> bool:
    if not url.startswith("http"):
        return False
    # Normalize
    url = url.split("#", 1)[0]
    if any(ext in url.lower() for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"]):
        return False
    try:
        host = url.split("//", 1)[1].split("/", 1)[0]
    except Exception:
        return False
    return host in ALLOWED_DOMAINS


def fetch(url: str, timeout: int = 20) -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        r = requests.get(url, timeout=timeout, headers=headers)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
            return r.text
        return None
    except Exception:
        return None


def clean_html(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    # Remove script/style/nav/asides
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string if soup.title else "").strip()
    text = soup.get_text("\n")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return title, text


def slugify(url: str) -> str:
    # Use path as slug
    path = url.split("//", 1)[-1]
    path = path.split("/", 1)[-1] if "/" in path else "index"
    if not path:
        path = "index"
    path = path.replace("/", "_")
    path = re.sub(r"[^\w\-\.]+", "-", path, flags=re.UNICODE)
    return path or "index"


def save_raw(url: str, title: str, text: str) -> str:
    filename = slugify(url) + ".txt"
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Source: {url}\n")
        if title:
            f.write(f"# Title: {title}\n")
        f.write("\n")
        f.write(text)
    return filepath


def chunk_words(words: List[str], target: int = 700, min_size: int = 500, overlap: int = 60) -> List[List[str]]:
    chunks: List[List[str]] = []
    i = 0
    n = len(words)
    while i < n:
        j = min(i + target, n)
        # Ensure minimum size unless at end
        if j - i < min_size and j < n:
            j = min(i + min_size, n)
        chunk = words[i:j]
        chunks.append(chunk)
        if j >= n:
            break
        i = max(j - overlap, i + 1)
    return chunks


def write_chunk(chunk_id: str, url: str, title: str, content: str) -> str:
    filename = f"{chunk_id}.txt"
    path = os.path.join(CHUNKS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Source: {url}\n")
        if title:
            f.write(f"# Title: {title}\n")
        f.write("\n")
        f.write(content)
    return path


def crawl(max_pages: int, delay_sec: float) -> List[Dict[str, str]]:
    seen: Set[str] = set()
    queue: deque[str] = deque(SEEDS)
    pages: List[Dict[str, str]] = []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        url = url.split("#", 1)[0]
        if url in seen or not is_allowed_url(url):
            continue
        seen.add(url)
        html = fetch(url)
        if not html:
            continue
        title, text = clean_html(html)
        if not text:
            continue
        save_raw(url, title, text)
        pages.append({"url": url, "title": title, "text": text})
        # Discover more links
        try:
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("/"):
                    # Relative to current host
                    host = url.split("//", 1)[1].split("/", 1)[0]
                    next_url = f"https://{host}{href}"
                elif href.startswith("http"):
                    next_url = href
                else:
                    continue
                if is_allowed_url(next_url):
                    queue.append(next_url)
        except Exception:
            pass
        if delay_sec > 0:
            time.sleep(delay_sec)
    return pages


def build_chunks_and_index(pages: List[Dict[str, str]], date_str: str) -> None:
    index: List[Dict[str, str]] = []
    counter = 1
    for p in pages:
        words = p["text"].split()
        parts = chunk_words(words)
        for part in parts:
            content = " ".join(part)
            chunk_id = f"chunk{counter:06d}"
            write_chunk(chunk_id, p["url"], p["title"], content)
            index.append(
                {
                    "id": chunk_id,
                    "source": p["url"],
                    "title": p["title"] or "",
                    "content": content,
                    "date": date_str,
                }
            )
            counter += 1
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RAG index for GUU from official sites")
    parser.add_argument("--max-pages", type=int, default=200, help="Max pages to crawl in total")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds")
    args = parser.parse_args()

    ensure_dirs()
    pages = crawl(max_pages=args.max_pages, delay_sec=args.delay)
    date_str = dt.date.today().isoformat()
    build_chunks_and_index(pages, date_str)
    print(f"Built index with {len(pages)} pages. Index at: {INDEX_PATH}")


if __name__ == "__main__":
    main()


