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

# Configure logging
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
        
        if self.config['exclude_keywords'] and any(keyword in url for keyword in self.config['exclude_keywords']):
            return False
        
        if self.config['include_keywords'] and not any(keyword in url for keyword in self.config['include_keywords']):
            return False
        
        return True

    async def process_url(self, session: ClientSession, url: str, depth: int, max_depth: int, 
                         semaphore: asyncio.Semaphore) -> Set[str]:
        if depth > max_depth or url in self.visited:
            return set()
        
        self.visited.add(url)
        
        async with semaphore:
            content = await self.fetch_url_with_retry(session, url)
        
        if content is None:
            return set()
            
        soup = BeautifulSoup(content, 'html.parser')
        found_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href.strip())
            if self.should_follow_url(full_url):
                found_urls.add(full_url)
                
        return found_urls

    async def get_all_pages(self) -> Set[str]:
        connector = TCPConnector(limit_per_host=self.config['connections_per_host'])
        async with ClientSession(connector=connector) as session:
            to_visit = {self.config['domain']}
            all_urls = set()
            max_depth = self.config['max_depth'] if self.config['max_depth'] is not None else float('inf')
            semaphore = asyncio.Semaphore(self.config['concurrent_requests'])
            
            for depth in range(int(max_depth) + 1):
                if not to_visit:
                    break
                    
                tasks = [
                    self.process_url(session, url, depth, max_depth, semaphore) 
                    for url in to_visit
                ]
                results = await asyncio.gather(*tasks)
                
                to_visit = set()
                for result in results:
                    all_urls.update(result)
                    to_visit.update(result - self.visited)
                    
                await asyncio.sleep(self.config['delay_between_requests'])
                
            return all_urls

    @staticmethod
    def split_text(text: str, max_length: Optional[int]) -> list[str]:
        return [text[i:i+max_length] for i in range(0, len(text), max_length)] if max_length else [text]

    async def run(self):
        logging.info(f"Starting scraper with domain: {self.config['domain']}")
        
        # Create output directory
        domain_name = urlparse(self.config['domain']).netloc
        directory_path = os.path.join(os.getcwd(), domain_name)
        os.makedirs(directory_path, exist_ok=True)
        
        csv_filename = os.path.join(directory_path, 'scraped_data.csv')
        
        # Get all URLs to scrape
        urls = await self.get_all_pages()
        logging.info(f"Found {len(urls)} URLs to scrape")
        
        if not urls:
            logging.warning("No URLs found to scrape. Check your domain and keyword settings.")
            return

        # Process and save content
        fieldnames = ['URL', 'Content', 'Chunk Number']
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            async with ClientSession() as session:
                for url in urls:
                    content = await self.fetch_url_with_retry(session, url)
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        if self.config['target_div']:
                            elements = soup.select(self.config['target_div'])
                            text = "\n".join([element.get_text(strip=True) for element in elements])
                        else:
                            text = soup.get_text(strip=True)
                        
                        chunks = self.split_text(text, self.config['split_length'])
                        for i, chunk in enumerate(chunks, 1):
                            content_hash = hashlib.md5(chunk.encode()).hexdigest()
                            if content_hash not in self.seen_content:
                                self.seen_content.add(content_hash)
                                writer.writerow({
                                    'URL': url,
                                    'Content': chunk,
                                    'Chunk Number': i
                                })
                        logging.info(f"Processed URL: {url}")
                    else:
                        logging.error(f"Failed to fetch content from {url}")
                        
                    await asyncio.sleep(self.config['delay_between_requests'])

        logging.info(f"All unique data saved to {csv_filename}")

def run_scraper(config: dict):
    """Run the web scraper with the given configuration."""
    scraper = WebScraper(config)
    asyncio.run(scraper.run())
