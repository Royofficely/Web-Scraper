# 🕷️ Officely AI Web Scraper

A powerful, recursive URL-smart web scraping tool designed to efficiently collect and organize content from websites. This tool is perfect for developers, researchers, and data enthusiasts who need to extract large amounts of textual data from web pages.

## Features

- 🌐 **Recursive URL Crawling**: Intelligently traverses websites to discover and scrape linked pages.
- 🎯 **Configurable Depth**: Set the maximum depth for URL recursion to control the scope of your scraping.
- 🔍 **Smart URL Filtering**: Include or exclude URLs based on keywords or prefixes.
- 📁 **Organized Output**: Automatically creates a directory structure based on the domain being scraped.
- 🛡️ **Respectful Scraping**: Implements user-agent rotation and retry logic with exponential backoff to respect website policies.
- ⚙️ **Highly Configurable**: Easy-to-use configuration file for customizing scraping behavior.

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
}
```

Adjust these settings according to your scraping needs.

## Output

The scraped content will be saved in a directory named after the domain you're scraping, with each page's content stored in a separate text file.

## Troubleshooting

If you encounter any issues:

1. Ensure you're in the project directory when running the install and run commands.
2. Check that all required files are present in the project directory.
3. Verify that you have the necessary permissions to install packages and write to the directory.
4. Make sure your virtual environment is activated if you're using one.
5. If you encounter 503 errors or other connection issues, the scraper will automatically retry with exponential backoff.
6. Check the console output for any error messages or debugging information.

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
