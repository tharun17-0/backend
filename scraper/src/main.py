from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

USER_AGENT = "FlyRankInternship-A9/1.0"

HEADERS = {
    "User-Agent": USER_AGENT
}


def get_cache_file(page_number: int) -> Path:
    return CACHE_DIR / f"catalogue-page-{page_number}.html"


def fetch_page(url: str, page_number: int) -> bytes:
    cache_file = get_cache_file(page_number)

    # Use cached HTML if available
    if cache_file.exists():
        content = cache_file.read_bytes()

        print(
            f"CACHE HIT page={page_number} bytes={len(content)}"
        )

        return content

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"FETCH page={page_number} url={url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Fetch failed for {url}: "
                f"HTTP {response.status_code}"
            )

        content = response.content

        cache_file.write_bytes(content)

        print(
            f"FETCHED page={page_number} bytes={len(content)}"
        )

        return content

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Request failed for {url}: {exc}"
        ) from exc


def parse_catalogue_page(html: bytes, current_url: str):
    soup = BeautifulSoup(html, "html.parser")

    book_urls = []

    # Find all book links on this catalogue page
    for link in soup.select("article.product_pod h3 a"):
        href = link.get("href")

        if not href:
            continue

        book_url = urljoin(current_url, href)

        if book_url not in book_urls:
            book_urls.append(book_url)

    # Find next catalogue page
    next_link = soup.select_one("li.next a")

    next_url = None

    if next_link:
        href = next_link.get("href")

        if href:
            next_url = urljoin(current_url, href)

    return book_urls, next_url


def discover_catalogue_pages():
    pages = []

    current_url = BASE_URL
    page_number = 1

    while len(pages) < 3:

        html = fetch_page(
            current_url,
            page_number
        )

        book_urls, next_url = parse_catalogue_page(
            html,
            current_url
        )

        pages.append(
            {
                "page_number": page_number,
                "url": current_url,
                "book_urls": book_urls
            }
        )

        print(
            f"PAGE {page_number}: "
            f"{len(book_urls)} books"
        )

        if next_url is None:
            break

        current_url = next_url
        page_number += 1

    return pages


def collect_book_urls(pages):
    unique_urls = []

    for page in pages:
        for url in page["book_urls"]:

            if url not in unique_urls:
                unique_urls.append(url)

    return unique_urls


def main():
    pages = discover_catalogue_pages()

    book_urls = collect_book_urls(pages)

    print()
    print(f"CATALOGUE PAGES: {len(pages)}")
    print(f"UNIQUE BOOK URLS: {len(book_urls)}")

    if len(pages) != 3:
        raise RuntimeError(
            f"Expected 3 catalogue pages, got {len(pages)}"
        )

    if len(book_urls) != 60:
        raise RuntimeError(
            f"Expected 60 unique book URLs, got {len(book_urls)}"
        )

    print("STAGE 2 CHECKPOINT PASSED")


if __name__ == "__main__":
    main()