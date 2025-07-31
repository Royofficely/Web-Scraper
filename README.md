# 🕷️ Officely AI Web Scraper

A powerful, recursive, URL-aware web scraping tool designed to efficiently extract structured content from websites. Ideal for developers, researchers, and data teams needing high-volume, high-quality data collection.

---

## 🚀 Features

* 🌐 **Recursive URL Crawling** – Traverse and extract content from linked pages.
* 🎯 **Configurable Depth** – Set max depth for recursion to control scope.
* 🔍 **Smart URL Filtering** – Include/exclude pages by keyword or prefix.
* 📁 **Organized Output** – Saves to structured folders by domain.
* 🛡️ **Respectful Crawling** – Includes retry logic, backoff, and pacing.
* ⚙️ **Highly Configurable** – All logic controlled via `config.py`.
* ✂️ **Text Splitting** – Splits long texts for better chunking.
* 🚫 **Protocol Exclusion** – Skip `mailto:`, `tel:`, `whatsapp:` etc.
* 🔁 **Robust Retry System** – With backoff and configurable retries.
* 🔀 **Concurrency Control** – Define max requests and per-host limits.
* 🕒 **Request Pacing** – Optional delays to avoid server overload.
* 🎯 **Targeted Extraction** – Focus only on specific divs per page.

---

## 🧪 Example: Targeting Specific Page Sections

Use the `target_divs` setting to extract only specific HTML components, like a title and article body:

```python
"target_divs": {
    "title": {
        "selector": "#main-content > section > div > div.relative... > header",
        "title": "Article Title"
    },
    "description": {
        "selector": "#main-content > section > div > div.relative... > div",
        "title": "Article Description"
    }
}
```

Each entry defines:

* `selector`: a CSS selector
* `title`: the label for output CSV

The scraper will match and extract only those components from the page.

---

## 🛠 Installation

```bash
git clone https://github.com/Royofficely/Web-Scraper.git
cd Web-Scraper
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
python agentim.py install
```

---

## ▶️ Usage

```bash
python agentim.py run
```

---

## ⚙️ Configuration (config.py)

```python
config = {
    "domain": "https://www.example.com",
    "include_keywords": ["blog"],
    "exclude_keywords": ["signup", "login"],
    "max_depth": 2,
    "target_divs": {...},
    "start_with": ["https://www.example.com/docs"],
    "split_length": 2000,
    "excluded_protocols": ['mailto:', 'tel:', 'whatsapp:'],
    "max_retries": 5,
    "base_delay": 1,
    "concurrent_requests": 10,
    "connections_per_host": 5,
    "delay_between_requests": 0.5
}
```

---

## 📦 Output

Scraped results are saved as CSV with columns:

* `URL`
* `Chunk`
* `Text`
* `Tag` (if `target_divs` used)

---

## 🧩 Troubleshooting

* Make sure you’re in the root directory when running.
* Increase `delay_between_requests` if rate-limited.
* Check log output for retries/errors.
* Use `start_with` to limit initial crawl scope.

---

## 🧑‍💻 Dev Setup

1. Install as above
2. Make edits in `officely_web_scraper/`
3. Run `agentim.py run` to test locally

---

## 🧱 Project Structure

```
.
├── agentim.py
├── officely_web_scraper/
│   ├── config.py
│   ├── scan.py
│   └── __init__.py
├── install.sh
├── requirements.txt
└── README.md
```

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue for any bugs or suggestions.

---

## 📄 License

MIT License • See `LICENSE` for details

---

Made with ❤️ by Roy Nativ @ [Officely AI](https://officely.ai)
