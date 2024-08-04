# Officely Web Scraper

A powerful, recursive URL-smart web scraping tool designed to efficiently collect and organize content from websites. This tool is perfect for developers, researchers, and data enthusiasts who need to extract large amounts of textual data from web pages.

## Features

- 🌐 **Recursive URL Crawling**: Intelligently traverses websites to discover and scrape linked pages.
- 🎯 **Configurable Depth**: Set the maximum depth for URL recursion to control the scope of your scraping.
- 🔍 **Smart URL Filtering**: Include or exclude URLs based on keywords or prefixes.
- 📁 **Organized Output**: Automatically creates a directory structure based on the domain being scraped.
- 🛡️ **Respectful Scraping**: Implements user-agent headers to respect website policies.
- ⚙️ **Highly Configurable**: Easy-to-use configuration file for customizing scraping behavior.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation and Setup

1. Clone this repository:
   ```
   git clone https://github.com/Royofficely/Web-Scraper.git
   cd Web-Scraper
   ```

2. Install the scraper and its dependencies:
   ```
   pip install .
   ```

   This command will install the package, its dependencies, and create the initial configuration.

## Usage

After installation, you can use the scraper from any directory:

1. Run the scraper:
   ```
   officely-scraper web scraper run
   ```

## Configuration

The scraper's behavior can be customized by editing the `config.py` file in the project directory:

```python
config = {
    "domain": "https://help.officely.ai",  # The starting URL for scraping
    "include_keywords": None,  # List of keywords to include in URLs
    "exclude_keywords": None,  # List of keywords to exclude from URLs
    "max_depth": 1,  # Maximum recursion depth (None for unlimited)
    "target_div": None,  # Specific div class to target (None for whole page)
    "start_with": None,  # List of URL prefixes to include
}
```

Adjust these settings according to your scraping needs.

## Output

The scraped content will be saved in a directory named after the domain you're scraping, with each page's content stored in a separate text file.

## Troubleshooting

If you encounter any issues:
1. Ensure you're in the project directory when running the install command.
2. Check that all required files (`agentim.py`, `scan.py`, `setup.py`, `requirements.txt`) are present in the project directory.
3. Verify that you have the necessary permissions to install packages and write to the directory.
4. If the `officely-scraper` command is not found after installation, try closing and reopening your terminal.

## Development

To set up the project for development:

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`
4. Run `officely-scraper web scraper install` to install in editable mode

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Created with ❤️ by [Roy Nativ/Officely AI]

For any questions or support, please open an issue on the GitHub repository.
