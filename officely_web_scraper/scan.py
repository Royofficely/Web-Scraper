import os
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def fetch_url_with_retry(session, url, max_retries=3, delay=5):
    if url.startswith('whatsapp://'):
        print(f"Skipping WhatsApp URL: {url}")
        return None
    
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt + 1 < max_retries:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retrying...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Failed to fetch {url} after {max_retries} attempts.")
                return None

def sanitize_filename(url):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        url = url.replace(char, '_')
    return url[:200]  # Limit filename length

def create_directory_for_domain(domain):
    domain_name = urlparse(domain).netloc
    directory_path = os.path.join(os.getcwd(), domain_name)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path

def should_follow_url(url, config):
    if url.startswith('whatsapp://'):
        return False
    if config['start_with']:
        if not url.startswith(config['start_with']):
            return False
    if config['exclude_keywords']:
        if any(keyword in url for keyword in config['exclude_keywords']):
            return False
    if config['include_keywords']:
        if not any(keyword in url for keyword in config['include_keywords']):
            return False
    return True

async def process_url(session, url, config, depth, visited, max_depth):
    if depth > max_depth or url in visited:
        return set()

    visited.add(url)
    
    content = await fetch_url_with_retry(session, url)
    if content is None:
        return set()

    soup = BeautifulSoup(content, 'html.parser')
    found_urls = set()

    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href.strip())
        if should_follow_url(full_url, config):
            found_urls.add(full_url)

    return found_urls

async def get_all_pages(config):
    async with aiohttp.ClientSession() as session:
        visited = set()
        to_visit = {config['domain']}
        all_urls = set()
        max_depth = config['max_depth'] if config['max_depth'] is not None else float('inf')

        for depth in range(int(max_depth) + 1):
            if not to_visit:
                break

            tasks = [process_url(session, url, config, depth, visited, max_depth) for url in to_visit]
            results = await asyncio.gather(*tasks)

            to_visit = set()
            for result in results:
                all_urls.update(result)
                to_visit.update(result - visited)

        return all_urls

def download_text(url, config):
    if url.startswith('whatsapp://'):
        return f"Skipped WhatsApp URL: {url}"
    
    try:
        headers = {'User-Agent': get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if config['target_div']:
            target_div = soup.find('div', class_=config['target_div'])
            if target_div:
                return target_div.get_text(strip=True)
            else:
                return f"Target div not found in {url}"
        else:
            return soup.get_text(strip=True)
    except requests.RequestException as e:
        return f"Error downloading content from {url}: {str(e)}"

async def run_scraper_async(config):
    print(f"Starting scraper with domain: {config['domain']}")
    domain_directory = create_directory_for_domain(config['domain'])
    urls = await get_all_pages(config)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_text, url, config) for url in urls]
        
        for future, url in zip(as_completed(futures), urls):
            text = future.result()
            filename = os.path.join(domain_directory, sanitize_filename(url) + ".txt")
            with open(filename, "w", encoding="utf-8") as file:
                file.write(f"URL: {url}\n\n{text}")
            print(f"Saved text from {url} to {filename}")

def run_scraper(config):
    asyncio.run(run_scraper_async(config.config))

def main():
    # This function is kept for backwards compatibility
    # but it's not used in the current setup
    pass

if __name__ == "__main__":
    main()
