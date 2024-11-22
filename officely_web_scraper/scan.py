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

    def __init__(self, config):
        self.config = config
        self.visited = set()
        self.results = []

    async def scan_website(self, url):
        async with aiohttp.ClientSession() as session:
            await self._scan_page(session, url, depth=0)
            # Add link discovery
            soup = BeautifulSoup(await self._fetch_page(session, url), 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                next_url = urljoin(url, link['href'])
                if next_url.startswith(self.config['domain']):
                    await self._scan_page(session, next_url, depth=1)
        return self.results

    async def _fetch_page(self, session, url):
        async with session.get(url) as response:
            return await response.text()

    async def _scan_page(self, session, url, depth):
        if url in self.visited:
            return
        self.visited.add(url)
        try:
            html = await self._fetch_page(session, url)
            soup = BeautifulSoup(html, 'html.parser')
            content = {}
            for div_key, div_info in self.config["target_divs"].items():
                elements = soup.select(div_info["selector"])
                if elements:
                    content[div_key] = {
                        "title": div_info["title"],
                        "text": [el.get_text(strip=True) for el in elements]
                    }
            self.results.append({"url": url, "content": content})
        except Exception as e:
            logging.error(f"Error scanning {url}: {e}")
