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

    def __init__(self, config: dict):
        self.config = config
        self.visited: Set[str] = set()
        self.seen_content: Set[str] = set()
        self.results = []

    async def scan_website(self, url: str):
        connector = aiohttp.TCPConnector(limit_per_host=self.config.get('connections_per_host', 5))
        async with aiohttp.ClientSession(connector=connector) as session:
            await self._scan_page(session, url, depth=0)
        return self.results

    async def _scan_page(self, session: aiohttp.ClientSession, url: str, depth: int):
        if url in self.visited or depth > self.config.get('max_depth', 3):
            return

        self.visited.add(url)
        try:
            headers = {'User-Agent': random.choice(self.USER_AGENTS)}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    page_data = {
                        "url": url,
                        "content": self._extract_content(soup)
                    }
                    
                    if page_data["content"]:
                        self.results.append(page_data)
                    
                    # Process links
                    links = soup.find_all('a', href=True)
                    tasks = []
                    for link in links:
                        next_url = urljoin(url, link['href'])
                        if next_url.startswith(self.config['domain']):
                            tasks.append(self._scan_page(session, next_url, depth + 1))
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                        
        except Exception as e:
            logging.error(f"Error scanning {url}: {e}")

    def _extract_content(self, soup: BeautifulSoup) -> dict:
        content = {}
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            content["main"] = {
                "title": "Main Content",
                "text": main_content.get_text(strip=True)
            }
            
        # Extract target divs if specified
        if self.config.get("target_divs"):
            for div_key, div_info in self.config["target_divs"].items():
                element = soup.select_one(div_info["selector"])
                if element:
                    content[div_key] = {
                        "title": div_info["title"],
                        "text": element.get_text(strip=True)
                    }
                    
        return content