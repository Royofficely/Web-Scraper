import os
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet
from aiohttp import ClientSession, TCPConnector
from aiohttp.client_exceptions import ClientResponseError
import logging

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def fetch_url_with_retry(session, url, config):
    for attempt in range(config['max_retries']):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', config['base_delay']))
                    logging.warning(f"Rate limited. Waiting for {retry_after} seconds before retrying...")
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                content = await response.read()
                encoding = response.charset or chardet.detect(content)['encoding']
                return content.decode(encoding, errors='replace')
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt + 1 < config['max_retries']:
                wait_time = config['base_delay'] * (2 ** attempt)  # Exponential backoff
                logging.info(f"Waiting {wait_time} seconds before retrying...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"Failed to fetch {url} after {config['max_retries']} attempts.")
                return None
        except Exception as e:
            logging.error(f"Unexpected error for {url}: {e}")
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
    if config['start_with'] and not url.startswith(config['start_with']):
        return False
    
    if config['exclude_keywords']:
        if any(keyword in url for keyword in config['exclude_keywords']):
            return False
    
    if config['include_keywords']:
        if not any(keyword in url for keyword in config['include_keywords']):
            return False
    
    if any(url.startswith(protocol) for protocol in config['excluded_protocols']):
        return False
    
    return True

async def process_url(session, url, config, depth, visited, max_depth, semaphore):
    if depth > max_depth or url in visited:
        return set()

    visited.add(url)
    
    async with semaphore:  # Use semaphore to limit concurrent requests
        content = await fetch_url_with_retry(session, url, config)
    
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
    connector = TCPConnector(limit_per_host=config['connections_per_host'])
    async with ClientSession(connector=connector) as session:
        visited = set()
        to_visit = {config['domain']}
        all_urls = set()
        max_depth = config['max_depth'] if config['max_depth'] is not None else float('inf')
        semaphore = asyncio.Semaphore(config['concurrent_requests'])

        for depth in range(int(max_depth) + 1):
            if not to_visit:
                break

            tasks = [process_url(session, url, config, depth, visited, max_depth, semaphore) for url in to_visit]
            results = await asyncio.gather(*tasks)

            to_visit = set()
            for result in results:
                all_urls.update(result)
                to_visit.update(result - visited)

            # Add a small delay between depth levels
            await asyncio.sleep(1)

        return all_urls

def download_text_with_retry(url, config):
    for attempt in range(config['max_retries']):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', config['base_delay']))
                logging.warning(f"Rate limited. Waiting for {retry_after} seconds before retrying...")
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()

            content = response.content
            encoding = response.encoding or chardet.detect(content)['encoding']
            html = content.decode(encoding, errors='replace')

            soup = BeautifulSoup(html, 'html.parser')

            if config['target_div']:
                result = {}
                for selector in config['target_div']:
                    elements = soup.select(selector)
                    text = "\n".join([element.get_text(strip=True) for element in elements])
                    result[selector] = text if text else "Not found"
                if all(value == "Not found" for value in result.values()):
                    logging.warning(f"No target divs found in {url}")
                    return None
                return (url, result)  # Return both URL and result
            else:
                return (url, {"full_text": soup.get_text(strip=True)})
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt + 1 < config['max_retries']:
                wait_time = config['base_delay'] * (2 ** attempt)  # Exponential backoff
                logging.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                logging.error(f"Error downloading content from {url}: {str(e)}")
                return None
        except Exception as e:
            logging.error(f"Unexpected error processing {url}: {str(e)}")
            return None

def split_text(text, max_length):
    """Split text into chunks of maximum length."""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)] if max_length else [text]

async def run_scraper_async(config):
    logging.info(f"Starting scraper with domain: {config['domain']}")
    domain_directory = create_directory_for_domain(config['domain'])
    urls = await get_all_pages(config)

    csv_filename = os.path.join(domain_directory, "scraped_data.csv")

    with ThreadPoolExecutor(max_workers=config['concurrent_requests']) as executor:
        futures = [executor.submit(download_text_with_retry, url, config) for url in urls if should_follow_url(url, config)]

        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['URL'] + config['target_div'] + ['Chunk Number']
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csv_writer.writeheader()

            for future in as_completed(futures):
                result = future.result()
                if result:
                    url, content = result
                    if content and all(content.get(selector) and content.get(selector) != "Not found" for selector in config['target_div']):
                        try:
                            # Determine the maximum number of chunks across all columns
                            max_chunks = max(len(split_text(content[selector], config['split_length'])) 
                                             for selector in config['target_div'])
                            
                            for i in range(max_chunks):
                                row = {'URL': url, 'Chunk Number': i + 1}
                                for selector in config['target_div']:
                                    chunks = split_text(content[selector], config['split_length'])
                                    row[selector] = chunks[i] if i < len(chunks) else ''
                                csv_writer.writerow(row)
                            logging.info(f"Saved text from {url} to CSV (in {max_chunks} chunks)")
                        except Exception as e:
                            logging.error(f"Error saving text from {url}: {str(e)}")
                    else:
                        logging.warning(f"No valid content found for {url}")
                else:
                    logging.warning(f"No valid URL or content found for a request")

                # Add a small delay between requests
                time.sleep(config['delay_between_requests'])

    logging.info(f"All data saved to {csv_filename}")

def run_scraper(config):
    asyncio.run(run_scraper_async(config))

if __name__ == "__main__":
    from config import config
    run_scraper(config)
