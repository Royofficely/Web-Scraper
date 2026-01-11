"""
Web Scraper - Fast async web scraper with recursive crawling.

This module provides a WebScraper class for crawling websites and extracting
text content into structured CSV files.

Features:
    - Async crawling with aiohttp
    - Proxy rotation support (custom list or ScraperAPI/Bright Data)
    - Circuit breaker for fail-fast on blocked sites
    - Rate limiting with exponential backoff
    - Content deduplication
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
from typing import Set, Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

import aiohttp
import chardet
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from aiohttp import TCPConnector, ClientSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class ConfigurationError(ScraperError):
    """Raised when configuration is invalid."""
    pass


class SecurityError(ScraperError):
    """Raised when a security check fails."""
    pass


class CircuitBreakerOpen(ScraperError):
    """Raised when circuit breaker is open due to too many failures."""
    pass


# =============================================================================
# Proxy Providers
# =============================================================================

class ProxyProvider(ABC):
    """Abstract base class for proxy providers."""

    @abstractmethod
    def get_proxy_url(self, target_url: str) -> str:
        """Get proxy URL or modified target URL for the request."""
        pass

    @abstractmethod
    def get_request_kwargs(self) -> Dict[str, Any]:
        """Get additional kwargs for aiohttp request."""
        pass


class NoProxy(ProxyProvider):
    """No proxy - direct connection."""

    def get_proxy_url(self, target_url: str) -> str:
        return target_url

    def get_request_kwargs(self) -> Dict[str, Any]:
        return {}


class ProxyList(ProxyProvider):
    """Rotating proxy list.

    Example:
        >>> proxies = ProxyList([
        ...     "http://user:pass@proxy1.example.com:8080",
        ...     "http://user:pass@proxy2.example.com:8080",
        ... ])
    """

    def __init__(self, proxies: List[str]):
        if not proxies:
            raise ConfigurationError("Proxy list cannot be empty")
        self.proxies = proxies
        self._index = 0

    def get_proxy_url(self, target_url: str) -> str:
        return target_url

    def get_request_kwargs(self) -> Dict[str, Any]:
        proxy = self.proxies[self._index % len(self.proxies)]
        self._index += 1
        return {"proxy": proxy}


class ScraperAPI(ProxyProvider):
    """ScraperAPI.com proxy service.

    Features:
        - Automatic proxy rotation
        - JavaScript rendering (optional)
        - Geo-targeting (optional)

    Example:
        >>> proxy = ScraperAPI(api_key="your_key", render_js=True, country="us")
    """

    BASE_URL = "http://api.scraperapi.com"

    def __init__(
        self,
        api_key: str,
        render_js: bool = False,
        country: Optional[str] = None,
        premium: bool = False,
    ):
        if not api_key:
            raise ConfigurationError("ScraperAPI requires an API key")
        self.api_key = api_key
        self.render_js = render_js
        self.country = country
        self.premium = premium

    def get_proxy_url(self, target_url: str) -> str:
        params = [f"api_key={self.api_key}", f"url={quote(target_url, safe='')}"]
        if self.render_js:
            params.append("render=true")
        if self.country:
            params.append(f"country_code={self.country}")
        if self.premium:
            params.append("premium=true")
        return f"{self.BASE_URL}?{'&'.join(params)}"

    def get_request_kwargs(self) -> Dict[str, Any]:
        return {}


class BrightData(ProxyProvider):
    """Bright Data (formerly Luminati) proxy service.

    Example:
        >>> proxy = BrightData(
        ...     username="user",
        ...     password="pass",
        ...     zone="residential",
        ...     country="us"
        ... )
    """

    def __init__(
        self,
        username: str,
        password: str,
        zone: str = "residential",
        country: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        if not username or not password:
            raise ConfigurationError("BrightData requires username and password")
        self.username = username
        self.password = password
        self.zone = zone
        self.country = country
        self.session_id = session_id or str(random.randint(1000000, 9999999))

    def get_proxy_url(self, target_url: str) -> str:
        return target_url

    def get_request_kwargs(self) -> Dict[str, Any]:
        # Build username with options
        user_parts = [f"{self.username}-zone-{self.zone}"]
        if self.country:
            user_parts.append(f"country-{self.country}")
        user_parts.append(f"session-{self.session_id}")

        username = "-".join(user_parts)
        proxy = f"http://{username}:{self.password}@brd.superproxy.io:22225"
        return {"proxy": proxy}


class Oxylabs(ProxyProvider):
    """Oxylabs proxy service.

    Example:
        >>> proxy = Oxylabs(username="user", password="pass", country="us")
    """

    def __init__(
        self,
        username: str,
        password: str,
        country: Optional[str] = None,
    ):
        if not username or not password:
            raise ConfigurationError("Oxylabs requires username and password")
        self.username = username
        self.password = password
        self.country = country

    def get_proxy_url(self, target_url: str) -> str:
        return target_url

    def get_request_kwargs(self) -> Dict[str, Any]:
        username = self.username
        if self.country:
            username = f"{self.username}-country-{self.country}"
        proxy = f"http://{username}:{self.password}@pr.oxylabs.io:7777"
        return {"proxy": proxy}


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitBreaker:
    """Circuit breaker to stop scraping when too many requests fail.

    Prevents wasting time and resources on sites that are blocking requests.

    States:
        - CLOSED: Normal operation, requests allowed
        - OPEN: Too many failures, requests blocked
        - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=10, recovery_timeout=60)
        >>> breaker.record_failure()  # Call on each failure
        >>> breaker.record_success()  # Call on each success
        >>> if breaker.is_open:
        ...     raise CircuitBreakerOpen("Too many failures")
    """

    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 10,
        success_threshold: int = 3,
        recovery_timeout: float = 60.0,
        failure_rate_threshold: float = 0.5,
        min_requests: int = 10,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures to open circuit
            success_threshold: Successes in half-open to close circuit
            recovery_timeout: Seconds before trying again after opening
            failure_rate_threshold: Failure rate (0-1) to open circuit
            min_requests: Minimum requests before checking failure rate
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_rate_threshold = failure_rate_threshold
        self.min_requests = min_requests

        self._state = self.State.CLOSED
        self._failures = 0
        self._successes = 0
        self._total_requests = 0
        self._total_failures = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> State:
        """Current circuit breaker state."""
        if self._state == self.State.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time:
                import time
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = self.State.HALF_OPEN
                    self._successes = 0
                    logger.info("Circuit breaker: HALF_OPEN (testing recovery)")
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == self.State.OPEN

    def record_success(self) -> None:
        """Record a successful request."""
        self._total_requests += 1
        self._failures = 0  # Reset consecutive failures

        if self._state == self.State.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self._state = self.State.CLOSED
                logger.info("Circuit breaker: CLOSED (recovered)")

    def record_failure(self) -> None:
        """Record a failed request."""
        import time
        self._total_requests += 1
        self._total_failures += 1
        self._failures += 1
        self._last_failure_time = time.time()

        # Check consecutive failures
        if self._failures >= self.failure_threshold:
            self._open_circuit("consecutive failures")
            return

        # Check failure rate
        if self._total_requests >= self.min_requests:
            failure_rate = self._total_failures / self._total_requests
            if failure_rate >= self.failure_rate_threshold:
                self._open_circuit(f"failure rate {failure_rate:.1%}")

    def _open_circuit(self, reason: str) -> None:
        """Open the circuit breaker."""
        if self._state != self.State.OPEN:
            self._state = self.State.OPEN
            logger.warning(f"Circuit breaker: OPEN ({reason})")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = self.State.CLOSED
        self._failures = 0
        self._successes = 0
        self._total_requests = 0
        self._total_failures = 0
        self._last_failure_time = None

    @property
    def stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "consecutive_failures": self._failures,
            "failure_rate": self._total_failures / max(1, self._total_requests),
        }


# =============================================================================
# Configuration
# =============================================================================

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
        proxy: Proxy provider instance (None for direct connection)
        circuit_breaker: Circuit breaker settings (None to disable)
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
    proxy: Optional[ProxyProvider] = None
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 10
    circuit_breaker_rate: float = 0.5

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

        # Block internal/private IPs (skip if using proxy)
        if self.proxy is None:
            try:
                hostname = parsed.hostname
                if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
                    raise SecurityError(f"Cannot scrape localhost: {hostname}")

                try:
                    ip = ipaddress.ip_address(hostname)
                    if ip.is_private or ip.is_loopback or ip.is_reserved:
                        raise SecurityError(f"Cannot scrape private/reserved IP: {hostname}")
                except ValueError:
                    try:
                        resolved_ip = socket.gethostbyname(hostname)
                        ip = ipaddress.ip_address(resolved_ip)
                        if ip.is_private or ip.is_loopback:
                            raise SecurityError(f"Domain {hostname} resolves to private IP: {resolved_ip}")
                    except socket.gaierror:
                        pass
            except SecurityError:
                raise
            except Exception:
                pass

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
        """
        if 'domain' not in config:
            raise ConfigurationError("'domain' is required in configuration")

        # Handle proxy configuration
        proxy = None
        proxy_config = config.get('proxy')
        if proxy_config:
            proxy_type = proxy_config.get('type', '').lower()
            if proxy_type == 'list':
                proxy = ProxyList(proxy_config.get('proxies', []))
            elif proxy_type == 'scraperapi':
                proxy = ScraperAPI(
                    api_key=proxy_config.get('api_key', ''),
                    render_js=proxy_config.get('render_js', False),
                    country=proxy_config.get('country'),
                    premium=proxy_config.get('premium', False),
                )
            elif proxy_type == 'brightdata':
                proxy = BrightData(
                    username=proxy_config.get('username', ''),
                    password=proxy_config.get('password', ''),
                    zone=proxy_config.get('zone', 'residential'),
                    country=proxy_config.get('country'),
                )
            elif proxy_type == 'oxylabs':
                proxy = Oxylabs(
                    username=proxy_config.get('username', ''),
                    password=proxy_config.get('password', ''),
                    country=proxy_config.get('country'),
                )

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
            proxy=proxy,
            circuit_breaker_enabled=config.get('circuit_breaker_enabled', True),
            circuit_breaker_threshold=config.get('circuit_breaker_threshold', 10),
            circuit_breaker_rate=config.get('circuit_breaker_rate', 0.5),
        )


# =============================================================================
# Web Scraper
# =============================================================================

class WebScraper:
    """Async web scraper with recursive crawling and content extraction.

    Features:
        - Concurrent requests with aiohttp
        - Recursive URL discovery
        - Configurable filtering by keywords
        - Rate limiting with exponential backoff
        - Content deduplication
        - User-agent rotation
        - Proxy support (ScraperAPI, Bright Data, Oxylabs, custom list)
        - Circuit breaker for fail-fast

    Example:
        >>> config = ScraperConfig(domain="https://example.com", max_depth=2)
        >>> scraper = WebScraper(config)
        >>> asyncio.run(scraper.run())

    With proxy:
        >>> config = ScraperConfig(
        ...     domain="https://example.com",
        ...     proxy=ScraperAPI(api_key="your_key")
        ... )
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
        self._proxy = config.proxy or NoProxy()

        # Initialize circuit breaker
        if config.circuit_breaker_enabled:
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=config.circuit_breaker_threshold,
                failure_rate_threshold=config.circuit_breaker_rate,
            )
        else:
            self._circuit_breaker = None

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

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
        """
        # Check circuit breaker
        if self._circuit_breaker and self._circuit_breaker.is_open:
            raise CircuitBreakerOpen(
                f"Circuit breaker open: {self._circuit_breaker.stats}"
            )

        for attempt in range(self.config.max_retries):
            try:
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)

                # Get URL and kwargs from proxy provider
                request_url = self._proxy.get_proxy_url(url)
                request_kwargs = self._proxy.get_request_kwargs()

                async with session.get(
                    request_url,
                    headers=headers,
                    timeout=timeout,
                    **request_kwargs
                ) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', self.config.base_delay))
                        logger.warning(f"Rate limited on {url}. Waiting {retry_after}s...")
                        if self._circuit_breaker:
                            self._circuit_breaker.record_failure()
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status >= 400:
                        logger.warning(f"HTTP {response.status} for {url}")
                        if self._circuit_breaker:
                            self._circuit_breaker.record_failure()
                        if attempt + 1 < self.config.max_retries:
                            wait_time = self.config.base_delay * (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(wait_time)
                            continue
                        return None

                    response.raise_for_status()
                    content = await response.read()
                    detected = chardet.detect(content)
                    encoding = response.charset or detected.get('encoding') or 'utf-8'

                    if self._circuit_breaker:
                        self._circuit_breaker.record_success()

                    return content.decode(encoding, errors='replace')

            except CircuitBreakerOpen:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries} failed for {url}: {e}")
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()
                if attempt + 1 < self.config.max_retries:
                    wait_time = self.config.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.config.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()
                return None

        return None

    def should_follow_url(self, url: str) -> bool:
        """Determine if URL should be crawled based on configuration filters."""
        if self.config.start_with and not url.startswith(self.config.start_with):
            return False

        if self.config.exclude_keywords:
            if any(keyword in url for keyword in self.config.exclude_keywords):
                return False

        if self.config.include_keywords:
            if not any(keyword in url for keyword in self.config.include_keywords):
                return False

        if any(url.startswith(protocol) for protocol in self.config.excluded_protocols):
            return False

        parsed_url = urlparse(url)
        if self._domain_netloc not in parsed_url.netloc:
            return False

        return True

    @staticmethod
    def extract_text_content(soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            element.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())

    @staticmethod
    def sanitize_csv_value(value: str) -> str:
        """Sanitize value to prevent CSV injection."""
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
        """Process a URL and extract links for further crawling."""
        if depth > max_depth or url in self.visited:
            return set()

        self.visited.add(url)

        async with semaphore:
            try:
                content = await self.fetch_url_with_retry(session, url)
            except CircuitBreakerOpen:
                return set()

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
        """Discover all pages to scrape by recursive crawling."""
        connector = TCPConnector(limit_per_host=self.config.connections_per_host)
        async with ClientSession(connector=connector) as session:
            to_visit = {self.config.domain}
            all_urls: Set[str] = set()
            max_depth = self.config.max_depth if self.config.max_depth is not None else float('inf')
            semaphore = asyncio.Semaphore(self.config.concurrent_requests)

            for depth in range(int(max_depth) + 1):
                if not to_visit:
                    break

                # Check circuit breaker
                if self._circuit_breaker and self._circuit_breaker.is_open:
                    logger.warning("Circuit breaker open - stopping crawl")
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
        """Split text into chunks of specified maximum length."""
        if not text:
            return []
        if not max_length:
            return [text]
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def _get_safe_output_directory(self) -> str:
        """Get safe output directory path, preventing path traversal."""
        domain_name = self._domain_netloc
        safe_name = re.sub(r'[^\w\-.]', '_', domain_name)
        safe_name = safe_name.lstrip('.')

        if not safe_name:
            safe_name = 'scraped_data'

        directory_path = os.path.join(os.getcwd(), safe_name)

        abs_cwd = os.path.abspath(os.getcwd())
        abs_dir = os.path.abspath(directory_path)
        if not abs_dir.startswith(abs_cwd):
            raise SecurityError(f"Path traversal detected: {directory_path}")

        return directory_path

    async def run(self) -> str:
        """Run the web scraper.

        Returns:
            Path to the output CSV file
        """
        logger.info(f"Starting scraper for: {self.config.domain}")
        if self.config.proxy:
            logger.info(f"Using proxy: {type(self.config.proxy).__name__}")

        directory_path = self._get_safe_output_directory()
        os.makedirs(directory_path, exist_ok=True)

        csv_filename = os.path.join(directory_path, 'scraped_data.csv')

        # Discover URLs
        try:
            urls = await self.get_all_pages()
        except CircuitBreakerOpen as e:
            logger.error(f"Scraping stopped: {e}")
            urls = set()

        logger.info(f"Found {len(urls)} URLs to scrape")

        if not urls:
            logger.warning("No URLs found. Check domain and filter settings.")
            if self._circuit_breaker:
                logger.info(f"Circuit breaker stats: {self._circuit_breaker.stats}")
            return csv_filename

        fieldnames = ['URL', 'Content', 'Chunk Number']

        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            async with ClientSession() as session:
                for i, url in enumerate(urls, 1):
                    # Check circuit breaker
                    if self._circuit_breaker and self._circuit_breaker.is_open:
                        logger.warning("Circuit breaker open - stopping content extraction")
                        break

                    try:
                        content = await self.fetch_url_with_retry(session, url)
                    except CircuitBreakerOpen:
                        logger.warning("Circuit breaker open - stopping content extraction")
                        break

                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        text_content = self.extract_text_content(soup)
                        chunks = self.split_text(text_content, self.config.split_length)

                        for chunk_num, chunk in enumerate(chunks, 1):
                            if not chunk:
                                continue

                            content_hash = hashlib.sha256(chunk.encode()).hexdigest()
                            if content_hash in self.seen_content:
                                continue
                            self.seen_content.add(content_hash)

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
        if self._circuit_breaker:
            logger.info(f"Circuit breaker stats: {self._circuit_breaker.stats}")
        return csv_filename


def run_scraper(config: Dict[str, Any]) -> str:
    """Run the web scraper with a configuration dictionary.

    Args:
        config: Dictionary with scraper configuration.
            Required: 'domain'
            Optional: See ScraperConfig for all options

    Returns:
        Path to the output CSV file

    Example (basic):
        >>> config = {
        ...     "domain": "https://example.com",
        ...     "max_depth": 2,
        ... }
        >>> run_scraper(config)

    Example (with ScraperAPI):
        >>> config = {
        ...     "domain": "https://example.com",
        ...     "proxy": {
        ...         "type": "scraperapi",
        ...         "api_key": "YOUR_API_KEY",
        ...         "render_js": True,
        ...     }
        ... }
        >>> run_scraper(config)

    Example (with Bright Data):
        >>> config = {
        ...     "domain": "https://example.com",
        ...     "proxy": {
        ...         "type": "brightdata",
        ...         "username": "user",
        ...         "password": "pass",
        ...         "country": "us",
        ...     }
        ... }
        >>> run_scraper(config)

    Example (with proxy list):
        >>> config = {
        ...     "domain": "https://example.com",
        ...     "proxy": {
        ...         "type": "list",
        ...         "proxies": [
        ...             "http://user:pass@proxy1:8080",
        ...             "http://user:pass@proxy2:8080",
        ...         ]
        ...     }
        ... }
        >>> run_scraper(config)
    """
    scraper_config = ScraperConfig.from_dict(config)
    scraper = WebScraper(scraper_config)
    return asyncio.run(scraper.run())


if __name__ == '__main__':
    from config import config
    run_scraper(config)
