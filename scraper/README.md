# FlyRank Week 5 — The Polite Scraper

A small Python scraping pipeline that collects the first three catalogue pages
from Books to Scrape, extracts book information, normalizes and validates the
records, caches fetched HTML, and produces clean JSON output.

## Target classification

### Target

https://books.toscrape.com/

Books to Scrape is a public practice sandbox designed for learning web scraping.

### Scope

This scraper processes only the first three catalogue pages and discovers the
60 books linked from those pages.

### Data collected

For each book, the scraper collects:

- title
- product_url
- price_text
- availability_text
- rating_text
- description
- source_page
- fetched_at

A normalized `price_gbp` value is also produced later in the pipeline.

### Robots check

I checked:

https://books.toscrape.com/robots.txt

Result: 404 / no robots file found.

A missing robots.txt file is not treated as permission to scrape other sites.

### Why this target is appropriate

Books to Scrape is explicitly provided as a practice sandbox for scraping,
so it is appropriate for this educational assignment.

I will not reuse this code on another site without checking its rules and
terms first.