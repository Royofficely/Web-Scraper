<h1 align="center">Web Scraper</h1>

<p align="center">
  <strong>Fast, async web scraper with recursive crawling, proxy support, and intelligent content extraction.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#proxy-support">Proxy Support</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#circuit-breaker">Circuit Breaker</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/async-aiohttp-green.svg" alt="Async">
  <img src="https://img.shields.io/github/license/Royofficely/Web-Scraper" alt="License">
  <img src="https://img.shields.io/github/stars/Royofficely/Web-Scraper?style=social" alt="Stars">
</p>

---

## What It Does

Crawl entire websites and extract clean text content into structured CSV files. Built for speed with async I/O, proxy rotation, and automatic failure detection.

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
| **Proxy Support** | Built-in support for ScraperAPI, Bright Data, Oxylabs, or custom proxy lists |
| **Circuit Breaker** | Automatically stops when site is blocking requests |
| **Recursive Discovery** | Follows links up to configurable depth |
| **Smart Filtering** | Include/exclude URLs by keywords |
| **Rate Limiting** | Configurable delays with exponential backoff + jitter |
| **Content Chunking** | Splits large pages into manageable pieces |
| **Duplicate Detection** | SHA-256 hashing prevents duplicate content |
| **Security** | SSRF protection, CSV injection prevention, path traversal prevention |

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

## Proxy Support

### ScraperAPI

```python
config = {
    "domain": "https://example.com",
    "proxy": {
        "type": "scraperapi",
        "api_key": "YOUR_API_KEY",
        "render_js": True,      # Optional: render JavaScript
        "country": "us",        # Optional: geo-targeting
    }
}
```

### Bright Data

```python
config = {
    "domain": "https://example.com",
    "proxy": {
        "type": "brightdata",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
        "zone": "residential",  # or "datacenter"
        "country": "us",        # Optional
    }
}
```

### Oxylabs

```python
config = {
    "domain": "https://example.com",
    "proxy": {
        "type": "oxylabs",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
        "country": "us",        # Optional
    }
}
```

### Custom Proxy List

```python
config = {
    "domain": "https://example.com",
    "proxy": {
        "type": "list",
        "proxies": [
            "http://user:pass@proxy1.example.com:8080",
            "http://user:pass@proxy2.example.com:8080",
        ]
    }
}
```

---

## Circuit Breaker

Automatically stops scraping when too many requests fail. Prevents wasting time on sites that are blocking you.

```python
config = {
    "domain": "https://example.com",
    "circuit_breaker_enabled": True,   # Default: True
    "circuit_breaker_threshold": 10,   # Stop after 10 consecutive failures
    "circuit_breaker_rate": 0.5,       # Or when 50% of requests fail
}
```

**Output when triggered:**
```
WARNING - Circuit breaker: OPEN (consecutive failures)
INFO - Circuit breaker stats: {'state': 'open', 'total_requests': 24, 'total_failures': 6}
```

---

## Configuration

All settings in `config.py`:

```python
config = {
    # Target
    "domain": "https://example.com",
    "max_depth": 3,                        # None = unlimited

    # Filtering
    "include_keywords": ["blog", "docs"],
    "exclude_keywords": ["login", "admin"],
    "start_with": None,

    # Rate Limiting
    "concurrent_requests": 10,
    "connections_per_host": 5,
    "delay_between_requests": 0.5,

    # Retry Logic
    "max_retries": 5,
    "base_delay": 1,                       # Doubles each attempt + jitter
    "timeout": 30,

    # Content
    "split_length": 2000,
    "excluded_protocols": ['mailto:', 'tel:', 'whatsapp:'],

    # Circuit Breaker
    "circuit_breaker_enabled": True,
    "circuit_breaker_threshold": 10,
    "circuit_breaker_rate": 0.5,

    # Proxy (optional)
    "proxy": None,                         # See Proxy Support section
}
```

---

## Usage

### Command Line

```bash
python scan.py
```

### As a Module

```python
from scan import run_scraper

config = {
    "domain": "https://example.com",
    "max_depth": 2,
}

output_file = run_scraper(config)
print(f"Saved to: {output_file}")
```

### With Proxy Provider Objects

```python
from scan import WebScraper, ScraperConfig, ScraperAPI
import asyncio

config = ScraperConfig(
    domain="https://example.com",
    max_depth=2,
    proxy=ScraperAPI(api_key="YOUR_KEY", render_js=True),
)

scraper = WebScraper(config)
output = asyncio.run(scraper.run())
```

---

## Output

Results saved as CSV:

| URL | Content | Chunk Number |
|-----|---------|--------------|
| https://example.com/page1 | Clean extracted text... | 1 |
| https://example.com/page1 | More text from same page... | 2 |

**Output location:** `./{domain}/scraped_data.csv`

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. Start with domain URL                               │
├─────────────────────────────────────────────────────────┤
│  2. Fetch page (async, retry + backoff, optional proxy) │
├─────────────────────────────────────────────────────────┤
│  3. Check circuit breaker (stop if too many failures)   │
├─────────────────────────────────────────────────────────┤
│  4. Extract links, filter by rules, add to queue        │
├─────────────────────────────────────────────────────────┤
│  5. Extract text, remove scripts/styles/nav             │
├─────────────────────────────────────────────────────────┤
│  6. Chunk, dedupe with SHA-256, save to CSV             │
└─────────────────────────────────────────────────────────┘
```

---

## Security Features

- **SSRF Protection** — Blocks requests to localhost, private IPs, internal networks
- **CSV Injection Prevention** — Sanitizes output to prevent formula injection
- **Path Traversal Prevention** — Validates output directory paths
- **Input Validation** — Validates all configuration parameters

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

## Tips

| Problem | Solution |
|---------|----------|
| Getting blocked | Use a proxy service (ScraperAPI, Bright Data) |
| Rate limited | Increase `delay_between_requests` |
| Too slow | Increase `concurrent_requests` (be respectful) |
| Missing pages | Increase `max_depth` or check `include_keywords` |
| Wasting time on blocked site | Enable circuit breaker (default: on) |

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
