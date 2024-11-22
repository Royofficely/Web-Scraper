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

class WebScraper:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
    ]

    def __init__(self, config):
        self.config = config
        self.visited = set()
        self.results = []
        self.session = None

    async def scan_website(self, url):
        connector = aiohttp.TCPConnector(limit_per_host=self.config.get('connections_per_host', 5))
        async with aiohttp.ClientSession(connector=connector, headers={'User-Agent': random.choice(self.USER_AGENTS)}) as session:
            self.session = session
            tasks = [self._process_url(url)]
            await asyncio.gather(*tasks)
        return self.results

    async def _process_url(self, url, depth=0):
        if url in self.visited or depth > self.config.get('max_depth', 3):
            return

        self.visited.add(url)
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract main content
                    main_content = soup.find('main')
                    if main_content:
                        self.results.append({
                            "url": url,
                            "content": {
                                "main": {
                                    "title": "Main Content",
                                    "text": main_content.get_text(strip=True)
                                }
                            }
                        })
                    
                    # Process next links
                    links = soup.find_all('a', href=True)
                    tasks = []
                    for link in links:
                        next_url = urljoin(url, link['href'])
                        if next_url.startswith(self.config['domain']):
                            tasks.append(self._process_url(next_url, depth + 1))
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                        
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
