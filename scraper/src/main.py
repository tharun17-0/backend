from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
import time

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

USER_AGENT = "FlyRankInternship-A9/1.0"

HEADERS = {
    "User-Agent": USER_AGENT
}

REQUEST_DELAY = 0.5


def get_cache_file(page_number: int) -> Path:
    return CACHE_DIR / f"catalogue-page-{page_number}.html"


def get_book_cache_file(book_number: int) -> Path:
    return CACHE_DIR / f"book-{book_number}.html"


def fetch_url(url: str, cache_file: Path) -> bytes:

    # Use cache if available
    if cache_file.exists():
        content = cache_file.read_bytes()

        print(
            f"CACHE HIT {cache_file.name} bytes={len(content)}"
        )

        return content

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"FETCH {url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Fetch failed: HTTP {response.status_code} "
                f"for {url}"
            )

        content = response.content

        cache_file.write_bytes(content)

        print(
            f"FETCHED {cache_file.name} bytes={len(content)}"
        )

        # Polite delay between real requests
        time.sleep(REQUEST_DELAY)

        return content

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Request failed for {url}: {exc}"
        ) from exc


def fetch_catalogue_page(url: str, page_number: int) -> bytes:

    cache_file = get_cache_file(page_number)

    return fetch_url(
        url,
        cache_file
    )


def parse_catalogue_page(
    html: bytes,
    current_url: str
):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    book_urls = []

    for link in soup.select(
        "article.product_pod h3 a"
    ):
        href = link.get("href")

        if not href:
            continue

        book_url = urljoin(
            current_url,
            href
        )

        if book_url not in book_urls:
            book_urls.append(book_url)

    next_link = soup.select_one(
        "li.next a"
    )

    next_url = None

    if next_link:
        href = next_link.get("href")

        if href:
            next_url = urljoin(
                current_url,
                href
            )

    return book_urls, next_url


def discover_catalogue_pages():

    pages = []

    current_url = BASE_URL
    page_number = 1

    while len(pages) < 3:

        html = fetch_catalogue_page(
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


def find_source_page(book_url: str, pages):

    for page in pages:

        if book_url in page["book_urls"]:
            return page["url"]

    return None


def extract_rating(product_pod):

    rating_element = product_pod.select_one(
        "p.star-rating"
    )

    if not rating_element:
        return None

    classes = rating_element.get("class", [])

    rating_names = {
        "One": "One",
        "Two": "Two",
        "Three": "Three",
        "Four": "Four",
        "Five": "Five"
    }

    for class_name in classes:

        if class_name in rating_names:
            return class_name

    return None


def extract_description(soup):

    heading = soup.select_one(
        "#product_description"
    )

    if not heading:
        return None

    description = heading.find_next_sibling("p")

    if not description:
        return None

    text = description.get_text(
        " ",
        strip=True
    )

    return text or None


def extract_book(
    html: bytes,
    product_url: str,
    source_page: str
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    title_element = soup.select_one("div.product_main h1")

    price_element = soup.select_one(
        "div.product_main .price_color"
    )

    availability_element = soup.select_one(
        "div.product_main .availability"
    )

    rating_element = soup.select_one(
        "div.product_main p.star-rating"
    )

    if not title_element:
        raise ValueError(
            "Missing title"
        )

    if not price_element:
        raise ValueError(
            "Missing price"
        )

    if not availability_element:
        raise ValueError(
            "Missing availability"
        )

    if not rating_element:
        raise ValueError(
            "Missing rating"
        )

    title = title_element.get_text(
        " ",
        strip=True
    )

    price_text = price_element.get_text(
        " ",
        strip=True
    )

    availability_text = availability_element.get_text(
        " ",
        strip=True
    )

    rating_text = extract_rating(
        soup
    )

    description = extract_description(
        soup
    )

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    return {
        "title": title,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "product_url": product_url,
        "source_page": source_page,
        "fetched_at": fetched_at
    }


def scrape_books(pages, book_urls):

    records = []

    for index, book_url in enumerate(
        book_urls,
        start=1
    ):

        cache_file = get_book_cache_file(
            index
        )

        source_page = find_source_page(
            book_url,
            pages
        )

        html = fetch_url(
            book_url,
            cache_file
        )

        try:

            record = extract_book(
                html,
                book_url,
                source_page
            )

            records.append(record)

            print(
                f"BOOK {index}/60: "
                f"{record['title']}"
            )

        except Exception as exc:

            print(
                f"ERROR BOOK {index}/60: "
                f"{book_url}: {exc}"
            )

    return records


def main():

    pages = discover_catalogue_pages()

    book_urls = collect_book_urls(
        pages
    )

    print()
    print(
        f"CATALOGUE PAGES: {len(pages)}"
    )

    print(
        f"UNIQUE BOOK URLS: {len(book_urls)}"
    )

    if len(pages) != 3:
        raise RuntimeError(
            f"Expected 3 catalogue pages, "
            f"got {len(pages)}"
        )

    if len(book_urls) != 60:
        raise RuntimeError(
            f"Expected 60 unique book URLs, "
            f"got {len(book_urls)}"
        )

    print()
    print("Starting book extraction...")

    records = scrape_books(
        pages,
        book_urls
    )

    print()
    print(
        f"RAW RECORDS: {len(records)}"
    )

    if len(records) != 60:
        raise RuntimeError(
            f"Expected 60 records, "
            f"got {len(records)}"
        )

    print(
        "STAGE 3 CHECKPOINT PASSED"
    )


if __name__ == "__main__":
    main()