"""
Web Scraper - Fast async web scraper with recursive crawling.

This module provides a WebScraper class for crawling websites and extracting
text content into structured CSV files.
"""

import os
import csv
import re
import asyncio
import logging
import hashlib
import random
import ipaddress
import socket
from typing import Set, Optional, Dict, Any, List
from dataclasses import dataclass, field

import aiohttp
import chardet
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from aiohttp import TCPConnector, ClientSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class ConfigurationError(ScraperError):
    """Raised when configuration is invalid."""
    pass


class SecurityError(ScraperError):
    """Raised when a security check fails."""
    pass


@dataclass
class ScraperConfig:
    """Configuration for the web scraper.

    Attributes:
        domain: Starting URL to crawl
        max_depth: Maximum recursion depth (None for unlimited)
        include_keywords: Only follow URLs containing these keywords
        exclude_keywords: Skip URLs containing these keywords
        start_with: Only follow URLs starting with this prefix
        split_length: Chunk size for content splitting
        excluded_protocols: Protocols to skip (mailto:, tel:, etc.)
        max_retries: Number of retry attempts for failed requests
        base_delay: Initial delay for exponential backoff
        concurrent_requests: Maximum parallel requests
        connections_per_host: Maximum connections per domain
        delay_between_requests: Delay between requests in seconds
        timeout: Request timeout in seconds
    """
    domain: str
    max_depth: Optional[int] = 3
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    start_with: Optional[str] = None
    split_length: Optional[int] = 2000
    excluded_protocols: List[str] = field(default_factory=lambda: ['mailto:', 'tel:', 'whatsapp:'])
    max_retries: int = 5
    base_delay: float = 1.0
    concurrent_requests: int = 10
    connections_per_host: int = 5
    delay_between_requests: float = 0.5
    timeout: int = 30

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        # Validate domain
        if not self.domain:
            raise ConfigurationError("Domain is required")

        parsed = urlparse(self.domain)
        if parsed.scheme not in ('http', 'https'):
            raise ConfigurationError(f"Invalid URL scheme: {parsed.scheme}. Use http or https.")

        if not parsed.netloc:
            raise ConfigurationError("Invalid domain: missing hostname")

        # Block internal/private IPs
        try:
            hostname = parsed.hostname
            if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
                raise SecurityError(f"Cannot scrape localhost: {hostname}")

            # Check for private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_reserved:
                    raise SecurityError(f"Cannot scrape private/reserved IP: {hostname}")
            except ValueError:
                # Not an IP address, it's a hostname - resolve and check
                try:
                    resolved_ip = socket.gethostbyname(hostname)
                    ip = ipaddress.ip_address(resolved_ip)
                    if ip.is_private or ip.is_loopback:
                        raise SecurityError(f"Domain {hostname} resolves to private IP: {resolved_ip}")
                except socket.gaierror:
                    pass  # Can't resolve, will fail later during scraping
        except SecurityError:
            raise
        except Exception:
            pass  # Other validation errors, continue

        # Validate numeric parameters
        if self.max_depth is not None and self.max_depth < 0:
            raise ConfigurationError("max_depth must be non-negative")

        if self.max_retries < 0:
            raise ConfigurationError("max_retries must be non-negative")

        if self.base_delay < 0:
            raise ConfigurationError("base_delay must be non-negative")

        if self.concurrent_requests < 1:
            raise ConfigurationError("concurrent_requests must be at least 1")

        if self.connections_per_host < 1:
            raise ConfigurationError("connections_per_host must be at least 1")

        if self.delay_between_requests < 0:
            raise ConfigurationError("delay_between_requests must be non-negative")

        if self.split_length is not None and self.split_length < 1:
            raise ConfigurationError("split_length must be positive or None")

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ScraperConfig':
        """Create ScraperConfig from a dictionary.

        Args:
            config: Dictionary with configuration values

        Returns:
            ScraperConfig instance

        Raises:
            ConfigurationError: If required fields are missing or invalid
        """
        if 'domain' not in config:
            raise ConfigurationError("'domain' is required in configuration")

        return cls(
            domain=config['domain'],
            max_depth=config.get('max_depth', 3),
            include_keywords=config.get('include_keywords'),
            exclude_keywords=config.get('exclude_keywords'),
            start_with=config.get('start_with'),
            split_length=config.get('split_length', 2000),
            excluded_protocols=config.get('excluded_protocols', ['mailto:', 'tel:', 'whatsapp:']),
            max_retries=config.get('max_retries', 5),
            base_delay=config.get('base_delay', 1.0),
            concurrent_requests=config.get('concurrent_requests', 10),
            connections_per_host=config.get('connections_per_host', 5),
            delay_between_requests=config.get('delay_between_requests', 0.5),
            timeout=config.get('timeout', 30),
        )


class WebScraper:
    """Async web scraper with recursive crawling and content extraction.

    Features:
        - Concurrent requests with aiohttp
        - Recursive URL discovery
        - Configurable filtering by keywords
        - Rate limiting with exponential backoff
        - Content deduplication
        - User-agent rotation

    Example:
        >>> config = ScraperConfig(domain="https://example.com", max_depth=2)
        >>> scraper = WebScraper(config)
        >>> asyncio.run(scraper.run())
    """

    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]

    def __init__(self, config: ScraperConfig) -> None:
        """Initialize the web scraper.

        Args:
            config: ScraperConfig instance with scraping parameters
        """
        self.config = config
        self.visited: Set[str] = set()
        self.seen_content: Set[str] = set()
        self._domain_netloc = urlparse(config.domain).netloc

    @staticmethod
    def get_random_user_agent() -> str:
        """Return a random user agent string."""
        return random.choice(WebScraper.USER_AGENTS)

    async def fetch_url_with_retry(self, session: ClientSession, url: str) -> Optional[str]:
        """Fetch URL content with retry logic and exponential backoff.

        Args:
            session: aiohttp ClientSession
            url: URL to fetch

        Returns:
            Page content as string, or None if all retries failed
        """
        for attempt in range(self.config.max_retries):
            try:
                headers = {'User-Agent': self.get_random_user_agent()}
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)

                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', self.config.base_delay))
                        logger.warning(f"Rate limited on {url}. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue

                    response.raise_for_status()
                    content = await response.read()
                    detected = chardet.detect(content)
                    encoding = response.charset or detected.get('encoding') or 'utf-8'
                    return content.decode(encoding, errors='replace')

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries} failed for {url}: {e}")
                if attempt + 1 < self.config.max_retries:
                    # Exponential backoff with jitter
                    wait_time = self.config.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

        return None

    def should_follow_url(self, url: str) -> bool:
        """Determine if URL should be crawled based on configuration filters.

        Args:
            url: Absolute URL to evaluate

        Returns:
            True if URL passes all filters, False otherwise
        """
        # Check start_with prefix
        if self.config.start_with and not url.startswith(self.config.start_with):
            return False

        # Check exclude keywords
        if self.config.exclude_keywords:
            if any(keyword in url for keyword in self.config.exclude_keywords):
                return False

        # Check include keywords
        if self.config.include_keywords:
            if not any(keyword in url for keyword in self.config.include_keywords):
                return False

        # Check excluded protocols
        if any(url.startswith(protocol) for protocol in self.config.excluded_protocols):
            return False

        # Check same domain
        parsed_url = urlparse(url)
        if self._domain_netloc not in parsed_url.netloc:
            return False

        return True

    @staticmethod
    def extract_text_content(soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML.

        Removes script, style, and other non-content elements.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Cleaned text content
        """
        # Remove non-content elements
        for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            element.decompose()

        # Get text and normalize whitespace
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())

    @staticmethod
    def sanitize_csv_value(value: str) -> str:
        """Sanitize value to prevent CSV injection.

        Prefixes dangerous characters with a single quote to prevent
        formula execution in spreadsheet applications.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string safe for CSV export
        """
        if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
            return f"'{value}"
        return value

    async def process_url(
        self,
        session: ClientSession,
        url: str,
        depth: int,
        max_depth: float,
        semaphore: asyncio.Semaphore
    ) -> Set[str]:
        """Process a URL and extract links for further crawling.

        Args:
            session: aiohttp ClientSession
            url: URL to process
            depth: Current crawl depth
            max_depth: Maximum allowed depth
            semaphore: Semaphore for rate limiting

        Returns:
            Set of discovered URLs to crawl
        """
        if depth > max_depth or url in self.visited:
            return set()

        self.visited.add(url)

        async with semaphore:
            content = await self.fetch_url_with_retry(session, url)

        if content is None:
            return set()

        soup = BeautifulSoup(content, 'html.parser')
        found_urls: Set[str] = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href.strip())
            if self.should_follow_url(full_url):
                found_urls.add(full_url)

        return found_urls

    async def get_all_pages(self) -> Set[str]:
        """Discover all pages to scrape by recursive crawling.

        Returns:
            Set of URLs discovered within the configured depth
        """
        connector = TCPConnector(limit_per_host=self.config.connections_per_host)
        async with ClientSession(connector=connector) as session:
            to_visit = {self.config.domain}
            all_urls: Set[str] = set()
            max_depth = self.config.max_depth if self.config.max_depth is not None else float('inf')
            semaphore = asyncio.Semaphore(self.config.concurrent_requests)

            for depth in range(int(max_depth) + 1):
                if not to_visit:
                    break

                logger.info(f"Crawling depth {depth}: {len(to_visit)} URLs")

                tasks = [
                    self.process_url(session, url, depth, max_depth, semaphore)
                    for url in to_visit
                ]
                results = await asyncio.gather(*tasks)

                to_visit = set()
                for result in results:
                    all_urls.update(result)
                    to_visit.update(result - self.visited)

                await asyncio.sleep(self.config.delay_between_requests)

            return all_urls

    @staticmethod
    def split_text(text: str, max_length: Optional[int]) -> List[str]:
        """Split text into chunks of specified maximum length.

        Args:
            text: Text to split
            max_length: Maximum chunk size, or None for no splitting

        Returns:
            List of text chunks
        """
        if not text:
            return []
        if not max_length:
            return [text]
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def _get_safe_output_directory(self) -> str:
        """Get safe output directory path, preventing path traversal.

        Returns:
            Safe directory path within current working directory
        """
        # Extract and sanitize domain name
        domain_name = self._domain_netloc
        # Remove any path traversal attempts
        safe_name = re.sub(r'[^\w\-.]', '_', domain_name)
        # Ensure it doesn't start with dots
        safe_name = safe_name.lstrip('.')

        if not safe_name:
            safe_name = 'scraped_data'

        directory_path = os.path.join(os.getcwd(), safe_name)

        # Verify the path is within current directory (prevent traversal)
        abs_cwd = os.path.abspath(os.getcwd())
        abs_dir = os.path.abspath(directory_path)
        if not abs_dir.startswith(abs_cwd):
            raise SecurityError(f"Path traversal detected: {directory_path}")

        return directory_path

    async def run(self) -> str:
        """Run the web scraper.

        Crawls the configured domain, extracts content, and saves to CSV.

        Returns:
            Path to the output CSV file
        """
        logger.info(f"Starting scraper for: {self.config.domain}")

        # Create safe output directory
        directory_path = self._get_safe_output_directory()
        os.makedirs(directory_path, exist_ok=True)

        csv_filename = os.path.join(directory_path, 'scraped_data.csv')

        # Discover URLs
        urls = await self.get_all_pages()
        logger.info(f"Found {len(urls)} URLs to scrape")

        if not urls:
            logger.warning("No URLs found. Check domain and filter settings.")
            return csv_filename

        fieldnames = ['URL', 'Content', 'Chunk Number']

        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            async with ClientSession() as session:
                for i, url in enumerate(urls, 1):
                    content = await self.fetch_url_with_retry(session, url)
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        text_content = self.extract_text_content(soup)
                        chunks = self.split_text(text_content, self.config.split_length)

                        for chunk_num, chunk in enumerate(chunks, 1):
                            if not chunk:
                                continue

                            # Deduplicate content
                            content_hash = hashlib.sha256(chunk.encode()).hexdigest()
                            if content_hash in self.seen_content:
                                continue
                            self.seen_content.add(content_hash)

                            # Write with CSV injection protection
                            row = {
                                'URL': self.sanitize_csv_value(url),
                                'Content': self.sanitize_csv_value(chunk),
                                'Chunk Number': chunk_num
                            }
                            writer.writerow(row)

                        logger.info(f"[{i}/{len(urls)}] Processed: {url}")
                    else:
                        logger.error(f"[{i}/{len(urls)}] Failed: {url}")

                    await asyncio.sleep(self.config.delay_between_requests)

        logger.info(f"Scraping complete. Output: {csv_filename}")
        return csv_filename


def run_scraper(config: Dict[str, Any]) -> str:
    """Run the web scraper with a configuration dictionary.

    Args:
        config: Dictionary with scraper configuration.
            Required: 'domain'
            Optional: See ScraperConfig for all options

    Returns:
        Path to the output CSV file

    Raises:
        ConfigurationError: If configuration is invalid
        SecurityError: If security check fails

    Example:
        >>> config = {
        ...     "domain": "https://example.com",
        ...     "max_depth": 2,
        ...     "concurrent_requests": 5,
        ... }
        >>> output_file = run_scraper(config)
    """
    scraper_config = ScraperConfig.from_dict(config)
    scraper = WebScraper(scraper_config)
    return asyncio.run(scraper.run())


if __name__ == '__main__':
    from config import config
    run_scraper(config)
