import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def fetch_url_with_retry(url, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt + 1 < max_retries:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch {url} after {max_retries} attempts.")
                return None

def sanitize_filename(url):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        url = url.replace(char, '_')
    return url

def create_directory_for_domain(domain):
    domain_name = urlparse(domain).netloc
    directory_path = os.path.join(os.getcwd(), domain_name)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path

def should_follow_url(url, config):
    print(f"Checking URL: {url}")
    if config.config['start_with']:
        if not any(url.startswith(prefix) for prefix in config.config['start_with']):
            print(f"Excluding URL, does not start with any specified prefixes: {url}")
            return False
    if config.config['exclude_keywords']:
        if any(keyword in url for keyword in config.config['exclude_keywords']):
            print(f"Excluding URL, contains excluded keywords: {url}")
            return False
    if config.config['include_keywords']:
        if not any(keyword in url for keyword in config.config['include_keywords']):
            print(f"Excluding URL, does not contain any included keywords: {url}")
            return False
    return True

def get_all_pages(url, config, depth=0):
    if config.config['max_depth'] is not None and depth > config.config['max_depth']:
        print(f"Max depth reached, stopping recursion at URL: {url}")
        return set()
    try:
        response = fetch_url_with_retry(url)
        if response is None or response.status_code != 200:
            print(f"Failed to fetch URL: {url}")
            return set()
        soup = BeautifulSoup(response.content, 'html.parser')
        found_urls = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href.strip())
            if should_follow_url(full_url, config):
                found_urls.add(full_url)
                found_urls.update(get_all_pages(full_url, config, depth + 1))
        return found_urls
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return set()

def download_text(url):
    response = fetch_url_with_retry(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(strip=True)
    else:
        return f"Error downloading content from {url}"

def run_scraper(config):
    print(f"Starting scraper with domain: {config.config['domain']}")
    domain_directory = create_directory_for_domain(config.config['domain'])
    urls = get_all_pages(config.config['domain'], config)
    for url in urls:
        filename = os.path.join(domain_directory, sanitize_filename(url) + ".txt")
        text = download_text(url)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"URL: {url}\n\n{text}")
        print(f"Saved text from {url} to {filename}")
        time.sleep(random.uniform(1, 3))  # Random delay between requests

def main():
    # This function is kept for backwards compatibility
    # but it's not used in the current setup
    pass

if __name__ == "__main__":
    main()
