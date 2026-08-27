from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
import json
import re
import time

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, HttpUrl


BASE_URL = "https://books.toscrape.com/"

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

BOOKS_FILE = OUTPUT_DIR / "books.json"

ERRORS_FILE = OUTPUT_DIR / "errors.json"

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

class BookRecord(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    title: str
    product_url: HttpUrl

    price_text: str
    price_gbp: float

    availability_text: str
    availability: str
    stock_count: int | None

    rating_text: str
    rating: int

    description: str | None

    source_page: HttpUrl
    fetched_at: datetime

def normalize_availability(
    availability_text: str
):
    text = availability_text.strip()

    match = re.search(
        r"\((\d+)\s+available\)",
        text,
        re.IGNORECASE
    )

    stock_count = None

    if match:
        stock_count = int(
            match.group(1)
        )

    if text.lower().startswith("in stock"):
        availability = "In stock"

    elif text.lower().startswith("out of stock"):
        availability = "Out of stock"

    else:
        availability = text

    return availability, stock_count

def normalize_record(raw_record: dict) -> dict:

    price_gbp = normalize_price(
        raw_record["price_text"]
    )

    rating = normalize_rating(
        raw_record["rating_text"]
    )

    availability, stock_count = normalize_availability(
        raw_record["availability_text"]
    )

    return {
        "title": raw_record["title"],
        "product_url": raw_record["product_url"],

        "price_text": raw_record["price_text"],
        "price_gbp": price_gbp,

        "availability_text": raw_record["availability_text"],
        "availability": availability,
        "stock_count": stock_count,

        "rating_text": raw_record["rating_text"],
        "rating": rating,

        "description": raw_record["description"],

        "source_page": raw_record["source_page"],
        "fetched_at": raw_record["fetched_at"]
    }

def validate_record(raw_record: dict):

    try:
        normalized = normalize_record(
            raw_record
        )
        validated = BookRecord.model_validate(
            normalized
        )
        return validated, None

    except Exception as exc:

        return None, str(exc)

def normalize_price(price_text: str) -> float:

    cleaned = price_text.replace("£", "").strip()

    return float(cleaned)
def normalize_rating(rating_text: str) -> int:

    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    if rating_text not in rating_map:
        raise ValueError(
            f"Unknown rating: {rating_text}"
        )

    return rating_map[rating_text]
def write_json(
    path: Path,
    data
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )
def save_valid_records(
    valid_records
):

    data = [
        record.model_dump(
            mode="json"
        )
        for record in valid_records
    ]

    write_json(
        BOOKS_FILE,
        data
    )
def save_errors(errors):

    write_json(
        ERRORS_FILE,
        errors
    )

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

    raw_records = scrape_books(
        pages,
        book_urls
    )

    print()
    print(
        f"RAW RECORDS: {len(raw_records)}"
    )

    valid_records = []

    errors = []

    for raw_record in raw_records:

        record, error = validate_record(
            raw_record
        )

        if record is not None:

            valid_records.append(
                record
            )

        else:

            errors.append(
                {
                    "product_url": raw_record.get(
                        "product_url"
                    ),
                    "reason": error
                }
            )

    save_valid_records(
        valid_records
    )

    save_errors(
        errors
    )

    print()
    print(
        f"VALID RECORDS: {len(valid_records)}"
    )

    print(
        f"INVALID RECORDS: {len(errors)}"
    )

    print(
        f"WROTE: {BOOKS_FILE}"
    )

    print(
        f"WROTE: {ERRORS_FILE}"
    )

    if len(valid_records) != 60:

        raise RuntimeError(
            f"Expected 60 valid records, "
            f"got {len(valid_records)}"
        )

    print()
    print(
        "STAGE 4 CHECKPOINT PASSED"
    )


if __name__ == "__main__":
    main()