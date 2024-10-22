config = {
    "domain": "https://example.com",  # The main domain URL for scraping
    "include_keywords": ["example"],  # List of keywords to include in URLs
    "exclude_keywords": None,  # List of keywords to exclude from URLs
    "max_depth": 1,  # Maximum recursion depth (None for unlimited)
    "target_div": None,  # Specific div class to target (None for whole page)
    "start_with": None,  # Filter by "start with" the url. For example: ["https://example.com/blog"]
    "split_length": None,  # Maximum length of text chunks for CSV rows
    "excluded_protocols": ['whatsapp:', 'tel:', 'mailto:'],  # Protocols to exclude from scraping
    "max_retries": 5,  # Maximum number of retry attempts for failed requests
    "base_delay": 1,  # Base delay (in seconds) for exponential backoff
    "concurrent_requests": 10,  # Maximum number of concurrent requests
    "connections_per_host": 5,  # Maximum number of connections per host
    "delay_between_requests": 0.5,  # Delay (in seconds) between individual requests
}
