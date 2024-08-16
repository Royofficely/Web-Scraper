# 🕷️ Officely AI Web Scraper

A powerful, recursive URL-smart web scraping tool designed to efficiently collect and organize content from websites. This tool is perfect for developers, researchers, and data enthusiasts who need to extract large amounts of textual data from web pages.

## Features

- 🌐 **Recursive URL Crawling**: Intelligently traverses websites to discover and scrape linked pages.
- 🎯 **Configurable Depth**: Set the maximum depth for URL recursion to control the scope of your scraping.
- 🔍 **Smart URL Filtering**: Include or exclude URLs based on keywords or prefixes.
- 📁 **Organized Output**: Automatically creates a directory structure based on the domain being scraped.
- 🛡️ **Respectful Scraping**: Implements user-agent rotation and retry logic with exponential backoff to respect website policies.
- ⚙️ **Highly Configurable**: Easy-to-use configuration file for customizing scraping behavior.
- 📊 **Text Splitting**: Automatically splits long texts into smaller chunks to avoid metadata size limits.
- 🚫 **Protocol Exclusion**: Easily exclude specific protocols (e.g., WhatsApp, tel, mailto) from scraping.
- 🔄 **Flexible Retry Mechanism**: Configurable maximum retries and base delay for failed requests.
- 🚦 **Concurrent Request Control**: Set limits on concurrent requests and connections per host.
- ⏱️ **Request Pacing**: Configurable delay between individual requests to prevent overwhelming target servers.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation and Setup

1. Clone this repository:
   ```
   git clone https://github.com/Royofficely/Web-Scraper.git
   ```
2. Change to the project directory:
   ```
   cd Web-Scraper
   ```
3. (Optional but recommended) Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
4. Install the scraper and its dependencies:
   ```
   python agentim.py install
   ```
   This command will install the package, its dependencies, and create the initial configuration.

## Usage

After installation, you can run the scraper from the project directory:
```
python agentim.py run
```

## Configuration

The scraper's behavior can be customized by editing the `config.py` file in the `officely_web_scraper` directory:

```python
config = {
    "domain": "https://www.example.com",  # The main domain URL for scraping
    "include_keywords": None,  # List of keywords to include in URLs
    "exclude_keywords": None,  # List of keywords to exclude from URLs
    "max_depth": 1,  # Maximum recursion depth (None for unlimited)
    "target_div": None,  # Specific div class to target (None for whole page)
    "start_with": None,  # Filter by "start with" the url. For example: ["https://example.com/blog"]
    "split_length": 2000,  # Maximum length of text chunks for CSV rows
    "excluded_protocols": ['whatsapp:', 'tel:', 'mailto:'],  # Protocols to exclude from scraping
    "max_retries": 5,  # Maximum number of retry attempts for failed requests
    "base_delay": 1,  # Base delay (in seconds) for exponential backoff
    "concurrent_requests": 10,  # Maximum number of concurrent requests
    "connections_per_host": 5,  # Maximum number of connections per host
    "delay_between_requests": 0.5,  # Delay (in seconds) between individual requests
}
```

Adjust these settings according to your scraping needs.

## Output

The scraped content will be saved in a CSV file within a directory named after the domain you're scraping. The CSV file will contain columns for the URL, scraped text, and chunk number (for split texts).

## Troubleshooting

If you encounter any issues:

1. Ensure you're in the project directory when running the install and run commands.
2. Check that all required files are present in the project directory.
3. Verify that you have the necessary permissions to install packages and write to the directory.
4. Make sure your virtual environment is activated if you're using one.
5. If you encounter 503 errors or other connection issues, the scraper will automatically retry with exponential backoff.
6. Check the console output for any error messages or debugging information.
7. Adjust the configuration parameters (e.g., `concurrent_requests`, `delay_between_requests`) if you're experiencing rate limiting or other access issues.

## Development

To set up the project for development:

1. Follow the installation steps above, using `python agentim.py install` for installation.
2. Make your changes to the code.
3. Run tests (if available) to ensure functionality.

## Project Structure

```
.
├── LICENSE
├── README.md
├── agentim.py
├── install.sh
├── officely-scraper
├── officely_web_scraper
│   ├── __init__.py
│   ├── config.py
│   └── scan.py
├── requirements.txt
└── setup.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Created with ❤️ by Roy Nativ/Officely AI

For any questions or support, please open an issue on the GitHub repository.
