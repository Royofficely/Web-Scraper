import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from . import config

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

def should_follow_url(url):
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

def get_all_pages(url, depth=0):
    if config.config['max_depth'] is not None and depth > config.config['max_depth']:
        print(f"Max depth reached, stopping recursion at URL: {url}")
        return set()
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch URL with status code {response.status_code}: {url}")
            return set()
        soup = BeautifulSoup(response.content, 'html.parser')
        found_urls = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href.strip())
            if should_follow_url(full_url):
                found_urls.add(full_url)
                found_urls.update(get_all_pages(full_url, depth + 1))
        return found_urls
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return set()

def download_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(strip=True)
        return text
    except Exception as e:
        return f"Error downloading content from {url}: {e}"

def run_scraper():
    domain_directory = create_directory_for_domain(config.config['domain'])
    urls = get_all_pages(config.config['domain'])
    for url in urls:
        filename = os.path.join(domain_directory, sanitize_filename(url) + ".txt")
        text = download_text(url)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"URL: {url}\n\n{text}")
        print(f"Saved text from {url} to {filename}")

def main():
    run_scraper()

if __name__ == "__main__":
    main()
