from pathlib import Path

import requests


BASE_URL = "https://books.toscrape.com/"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

USER_AGENT = "FlyRankInternship-A9/1.0"


def fetch_page():
    # Use cached HTML if it already exists
    if CACHE_FILE.exists():
        content = CACHE_FILE.read_bytes()

        print(f"CACHE HIT bytes={len(content)}")

        return content

    # Create cache directory if needed
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": USER_AGENT
    }

    print(f"FETCH {BASE_URL}")

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            timeout=10
        )

        # Only HTTP 200 is considered successful
        if response.status_code != 200:
            raise RuntimeError(
                f"Fetch failed: HTTP {response.status_code}"
            )

        content = response.content

        # Save HTML to cache
        CACHE_FILE.write_bytes(content)

        print(f"FETCHED bytes={len(content)}")

        return content

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Request failed: {exc}"
        ) from exc


def main():
    fetch_page()


if __name__ == "__main__":
    main()