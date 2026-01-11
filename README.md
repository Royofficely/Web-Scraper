<h1 align="center">Web Scraper</h1>

<p align="center">
  <strong>Fast, async web scraper with recursive crawling and intelligent content extraction.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#usage">Usage</a> •
  <a href="#output">Output</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/async-aiohttp-green.svg" alt="Async">
  <img src="https://img.shields.io/github/license/Royofficely/Web-Scraper" alt="License">
  <img src="https://img.shields.io/github/stars/Royofficely/Web-Scraper?style=social" alt="Stars">
</p>

---

## What It Does

Crawl entire websites and extract clean text content into structured CSV files. Built for speed with async I/O and respectful rate limiting.

```
Input:  https://docs.example.com
Output: 847 pages → clean CSV with URL, content, chunks
Time:   ~3 minutes
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Async Crawling** | Concurrent requests with `aiohttp` for 10x faster scraping |
| **Recursive Discovery** | Follows links up to configurable depth |
| **Smart Filtering** | Include/exclude URLs by keywords |
| **Rate Limiting** | Configurable delays and retry with exponential backoff |
| **Content Chunking** | Splits large pages into manageable pieces |
| **Duplicate Detection** | MD5 hashing prevents duplicate content |
| **User-Agent Rotation** | Randomized headers to avoid blocks |

---

## Quick Start

**1. Clone and install**

```bash
git clone https://github.com/Royofficely/Web-Scraper.git
cd Web-Scraper
pip install -r requirements.txt
```

**2. Configure target**

Edit `config.py`:

```python
config = {
    "domain": "https://docs.example.com",
    "max_depth": 3,
}
```

**3. Run**

```bash
python scan.py
```

Output saved to `./docs.example.com/scraped_data.csv`

---

## Configuration

All settings in `config.py`:

```python
config = {
    # Target
    "domain": "https://example.com",      # Starting URL
    "max_depth": 3,                        # How deep to crawl (None = unlimited)

    # Filtering
    "include_keywords": ["blog", "docs"],  # Only URLs containing these
    "exclude_keywords": ["login", "admin"], # Skip URLs containing these
    "start_with": None,                    # Only URLs starting with this prefix

    # Rate Limiting
    "concurrent_requests": 10,             # Max parallel requests
    "connections_per_host": 5,             # Max connections per domain
    "delay_between_requests": 0.5,         # Seconds between requests

    # Retry Logic
    "max_retries": 5,                      # Retry failed requests
    "base_delay": 1,                       # Initial retry delay (doubles each attempt)

    # Content
    "split_length": 2000,                  # Chunk size (chars). None = no splitting
    "excluded_protocols": ['mailto:', 'tel:', 'whatsapp:'],
}
```

---

## Usage

### Basic Crawl

```bash
python scan.py
```

### As a Module

```python
from scan import WebScraper, run_scraper

config = {
    "domain": "https://example.com",
    "max_depth": 2,
    "include_keywords": ["api"],
    "concurrent_requests": 5,
    "delay_between_requests": 1,
    "max_retries": 3,
    "base_delay": 1,
    "split_length": 2000,
    "connections_per_host": 5,
    "excluded_protocols": ['mailto:', 'tel:'],
    "exclude_keywords": None,
    "start_with": None,
}

run_scraper(config)
```

---

## Output

Results saved as CSV:

| URL | Content | Chunk Number |
|-----|---------|--------------|
| https://example.com/page1 | Clean extracted text... | 1 |
| https://example.com/page1 | More text from same page... | 2 |
| https://example.com/page2 | Another page content... | 1 |

**Output location:** `./{domain}/scraped_data.csv`

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. Start with domain URL                               │
├─────────────────────────────────────────────────────────┤
│  2. Fetch page (async, with retry + backoff)            │
├─────────────────────────────────────────────────────────┤
│  3. Extract all links, filter by rules                  │
├─────────────────────────────────────────────────────────┤
│  4. Add new URLs to queue (respect max_depth)           │
├─────────────────────────────────────────────────────────┤
│  5. Extract text content, remove scripts/styles         │
├─────────────────────────────────────────────────────────┤
│  6. Chunk content, dedupe with MD5, save to CSV         │
└─────────────────────────────────────────────────────────┘
```

---

## Use Cases

- **Training Data** — Collect text for ML/LLM fine-tuning
- **Documentation** — Mirror docs sites for offline access
- **Content Audit** — Inventory all pages on a domain
- **SEO Analysis** — Extract content structure at scale
- **Knowledge Base** — Build searchable content archives

---

## Requirements

- Python 3.8+
- aiohttp
- beautifulsoup4
- chardet

```bash
pip install aiohttp beautifulsoup4 chardet
```

---

## Project Structure

```
Web-Scraper/
├── scan.py           # Main scraper class
├── config.py         # Configuration
├── requirements.txt  # Dependencies
└── README.md
```

---

## Tips

- **Getting rate limited?** Increase `delay_between_requests`
- **Too slow?** Increase `concurrent_requests` (be respectful)
- **Missing pages?** Increase `max_depth` or check `include_keywords`
- **Large site?** Use `start_with` to scope to a section

---

## Contributing

PRs welcome. Please open an issue first for major changes.

---

## License

MIT

---

<p align="center">
  Built by <a href="https://github.com/Royofficely">Roy Nativ</a>
</p>
