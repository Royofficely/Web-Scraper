<h1 align="center">Web Scraper</h1>

<h4 align="center">Fast, async web scraper for extracting clean text from entire websites.</h4>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  </a>
  <a href="https://pypi.org/project/aiohttp/">
    <img src="https://img.shields.io/badge/async-aiohttp-green.svg" alt="aiohttp">
  </a>
  <a href="https://github.com/Royofficely/Web-Scraper/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Royofficely/Web-Scraper" alt="License">
  </a>
  <a href="https://github.com/Royofficely/Web-Scraper/stargazers">
    <img src="https://img.shields.io/github/stars/Royofficely/Web-Scraper?style=social" alt="Stars">
  </a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-why-web-scraper">Why Web Scraper</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-proxy-support">Proxy</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## Quick Start

```bash
# Install
git clone https://github.com/Royofficely/Web-Scraper.git
cd Web-Scraper && pip install -r requirements.txt

# Configure (edit config.py)
# domain = "https://docs.example.com"

# Run
python scan.py
```

**That's it.** Output saved to `./docs.example.com/scraped_data.csv`

---

## Why Web Scraper?

| Problem | How We Solve It |
|---------|-----------------|
| **Slow scraping** | Async I/O with `aiohttp` - 10x faster than sync requests |
| **Getting blocked** | User-agent rotation, rate limiting, optional proxy support |
| **Wasting time on blocked sites** | Circuit breaker auto-stops after consecutive failures |
| **Duplicate content** | SHA-256 deduplication across all pages |
| **Messy output** | Clean text extraction, removes scripts/styles/nav |
| **Security concerns** | SSRF protection, CSV injection prevention, input validation |

---

## Features

```
Async Crawling        Concurrent requests for maximum speed
Recursive Discovery   Follows links up to configurable depth
Smart Filtering       Include/exclude URLs by keywords
Content Chunking      Splits large pages into manageable pieces
Rate Limiting         Exponential backoff + jitter
Circuit Breaker       Auto-stops when site blocks requests
Proxy Support         ScraperAPI, Bright Data, Oxylabs, custom lists (optional)
Security              SSRF protection, CSV injection prevention
```

---

## Example

### Basic Usage

```python
# config.py
config = {
    "domain": "https://docs.example.com",
    "max_depth": 3,
    "include_keywords": ["docs", "guide"],
    "exclude_keywords": ["login", "admin"],
}
```

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
# => ./example.com/scraped_data.csv
```

### Output Format

| URL | Content | Chunk Number |
|-----|---------|--------------|
| https://example.com/page1 | Clean extracted text from the page... | 1 |
| https://example.com/page1 | More content from the same page... | 2 |
| https://example.com/page2 | Content from another page... | 1 |

---

## Configuration

```python
config = {
    # Target
    "domain": "https://example.com",    # Required
    "max_depth": 3,                      # None = unlimited

    # Filtering
    "include_keywords": ["blog"],        # Only crawl URLs containing these
    "exclude_keywords": ["login"],       # Skip URLs containing these

    # Performance
    "concurrent_requests": 10,           # Parallel requests
    "delay_between_requests": 0.5,       # Seconds between requests

    # Reliability
    "max_retries": 5,                    # Retry failed requests
    "circuit_breaker_threshold": 10,     # Stop after N consecutive failures

    # Proxy (optional)
    "proxy": None,                       # See Proxy Support section
}
```

<details>
<summary><strong>View all configuration options</strong></summary>

```python
config = {
    # Target
    "domain": "https://example.com",
    "max_depth": 3,

    # Filtering
    "include_keywords": None,
    "exclude_keywords": None,
    "start_with": None,
    "excluded_protocols": ['mailto:', 'tel:', 'whatsapp:'],

    # Performance
    "concurrent_requests": 10,
    "connections_per_host": 5,
    "delay_between_requests": 0.5,

    # Reliability
    "max_retries": 5,
    "base_delay": 1,
    "timeout": 30,

    # Circuit Breaker
    "circuit_breaker_enabled": True,
    "circuit_breaker_threshold": 10,
    "circuit_breaker_rate": 0.5,

    # Content
    "split_length": 2000,

    # Proxy
    "proxy": None,
}
```

</details>

---

## Proxy Support

> **Proxy is optional.** The scraper works great without it. Only use if you're getting blocked.

<details>
<summary><strong>ScraperAPI</strong></summary>

```python
"proxy": {
    "type": "scraperapi",
    "api_key": "YOUR_API_KEY",
    "render_js": True,
    "country": "us",
}
```

</details>

<details>
<summary><strong>Bright Data</strong></summary>

```python
"proxy": {
    "type": "brightdata",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "zone": "residential",
    "country": "us",
}
```

</details>

<details>
<summary><strong>Oxylabs</strong></summary>

```python
"proxy": {
    "type": "oxylabs",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "country": "us",
}
```

</details>

<details>
<summary><strong>Custom Proxy List</strong></summary>

```python
"proxy": {
    "type": "list",
    "proxies": [
        "http://user:pass@proxy1.example.com:8080",
        "http://user:pass@proxy2.example.com:8080",
    ]
}
```

</details>

---

## Circuit Breaker

Automatically stops when the site is blocking requests:

```
INFO  - Crawling depth 0: 1 URLs
INFO  - Crawling depth 1: 24 URLs
WARN  - HTTP 403 for https://example.com/page15
WARN  - HTTP 403 for https://example.com/page16
WARN  - Circuit breaker: OPEN (consecutive failures)
INFO  - Circuit breaker stats: {'state': 'open', 'total_requests': 24, 'failures': 10}
```

---

## Use Cases

| Use Case | Description |
|----------|-------------|
| **LLM Training Data** | Collect text for fine-tuning language models |
| **Documentation Mirror** | Archive docs sites for offline access |
| **Content Audit** | Inventory all pages on a domain |
| **SEO Analysis** | Extract content structure at scale |
| **Knowledge Base** | Build searchable content archives |
| **RAG Pipelines** | Feed content to retrieval-augmented generation |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Getting blocked | Add proxy or increase `delay_between_requests` |
| Rate limited (429) | Increase `delay_between_requests` to 2-5 seconds |
| Too slow | Increase `concurrent_requests` (be respectful) |
| Missing pages | Increase `max_depth` or adjust `include_keywords` |
| Circuit breaker triggers | Site is blocking - try proxy or reduce concurrency |

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

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## AI Prompt

Copy this to quickly set up scraping with AI assistants:

```
I need to scrape a website. Use the Web Scraper from github.com/Royofficely/Web-Scraper

Target: [YOUR_URL]
Depth: [1-5]
Include pages containing: [KEYWORDS or "all"]
Exclude: [KEYWORDS or "none"]

Clone, configure config.py, run scan.py, output to CSV.
No proxy needed unless I'm getting blocked.
```

---

<p align="center">
  <sub>Built by <a href="https://github.com/Royofficely">Roy Nativ</a> at <a href="https://officely.ai">Officely AI</a></sub>
</p>

<p align="center">
  <a href="https://github.com/Royofficely/Web-Scraper/issues">Report Bug</a> •
  <a href="https://github.com/Royofficely/Web-Scraper/issues">Request Feature</a>
</p>
