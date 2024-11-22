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
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    ]

    def __init__(self, config):
        self.config = config
        self.visited = set()
        self.results = []

    async def scan_website(self, url):
        async with aiohttp.ClientSession(headers={'User-Agent': random.choice(self.USER_AGENTS)}) as session:
            await self._process_url(session, url)
        return self.results

    async def _process_url(self, session, url, depth=0):
        if depth > self.config.get('max_depth', 3) or url in self.visited:
            return
        
        self.visited.add(url)
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    content = {}
                    for div_key, div_info in self.config["target_divs"].items():
                        elements = soup.select(div_info["selector"])
                        if elements:
                            content[div_key] = {
                                "title": div_info["title"],
                                "text": [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]
                            }
                    
                    if content:
                        self.results.append({"url": url, "content": content})
                    
                    links = soup.find_all('a', href=True)
                    for link in links:
                        next_url = urljoin(url, link['href'])
                        if next_url.startswith(self.config['domain']):
                            await self._process_url(session, next_url, depth + 1)
                            
        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
