import os
import csv
import asyncio
import logging
import aiohttp
import chardet
import hashlib
import random
from typing import Set, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from aiohttp import TCPConnector, ClientSession

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WebScraper:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    ]

    def __init__(self, config: dict):
        self.config = config
        self.visited: Set[str] = set()
        self.seen_content: Set[str] = set()
        self.results = []

    @staticmethod
    def get_random_user_agent() -> str:
        return random.choice(WebScraper.USER_AGENTS)

    async def fetch_url_with_retry(self, session: ClientSession, url: str) -> Optional[str]:
        for attempt in range(self.config['max_retries']):
            try:
                headers = {'User-Agent': self.get_random_user_agent()}
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', self.config['base_delay']))
                        logging.warning(f"Rate limited. Waiting for {retry_after} seconds before retrying...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    content = await response.read()
                    encoding = response.charset or chardet.detect(content)['encoding']
                    return content.decode(encoding, errors='replace')
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt + 1 < self.config['max_retries']:
                    wait_time = self.config['base_delay'] * (2 ** attempt)
                    logging.info(f"Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch {url} after {self.config['max_retries']} attempts.")
                    return None
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {e}")
                return None

    def should_follow_url(self, url: str) -> bool:
        if self.config.get('start_with') and not url.startswith(self.config['start_with']):
            return False
        
        if self.config.get('exclude_keywords') and any(keyword in url for keyword in self.config['exclude_keywords']):
            return False
        
        if self.config.get('include_keywords') and not any(keyword in url for keyword in self.config['include_keywords']):
            return False
        
        parsed_url = urlparse(url)
        if any(url.startswith(protocol) for protocol in self.config.get('excluded_protocols', [])):
            return False
            
        domain_name = urlparse(self.config['domain']).netloc
        if domain_name not in parsed_url.netloc:
            return False
        
        return True

    def extract_text_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())

    async def scan_website(self, url: str):
        connector = TCPConnector(limit_per_host=self.config.get('connections_per_host', 5))
        async with ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(self.config.get('concurrent_requests', 10))
            await self._process_url(session, url, 0, semaphore)
        return self.results

    async def _process_url(self, session: ClientSession, url: str, depth: int, semaphore: asyncio.Semaphore):
        if depth > self.config.get('max_depth', 3) or url in self.visited:
            return

        self.visited.add(url)
        
        async with semaphore:
            content = await self.fetch_url_with_retry(session, url)
            
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            text_content = self.extract_text_content(soup)
            
            if text_content:
                content_hash = hashlib.md5(text_content.encode()).hexdigest()
                if content_hash not in self.seen_content:
                    self.seen_content.add(content_hash)
                    self.results.append({
                        "url": url,
                        "content": {
                            "main": {
                                "title": soup.title.string if soup.title else "No Title",
                                "text": text_content
                            }
                        }
                    })
            
            tasks = []
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])
                if self.should_follow_url(next_url):
                    tasks.append(self._process_url(session, next_url, depth + 1, semaphore))
            
            if tasks:
                await asyncio.gather(*tasks)
                await asyncio.sleep(self.config.get('delay_between_requests', 0.5))

def run_scraper(config: dict):
    scraper = WebScraper(config)
    asyncio.run(scraper.run())
