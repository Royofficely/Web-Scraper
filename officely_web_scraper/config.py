config = {
    "domain": "https://help.example.com",  
    "include_keywords": ["example"],  # Added relevant keywords
    "exclude_keywords": None,
    "max_depth": 1,
    "target_div": None,
    "start_with": None,
    "split_length": 2000,
    "excluded_protocols": ['whatsapp:', 'tel:', 'mailto:'],
    "max_retries": 5,
    "base_delay": 1,
    "concurrent_requests": 10,
    "connections_per_host": 5,
    "delay_between_requests": 0.5,
}


# config = {
#     "domain": "https://help.officely.ai",
#     "include_keywords": ["officely","articles"],
#     "exclude_keywords": None,
#     "max_depth": 1,
#     "target_divs": {
#         "title": {
#             "selector": "#main-content > section > div > div.relative.z-3.w-full.lg\:max-w-160 > div:nth-child(2) > div > div.mb-10.max-lg\:mb-6 > div > div.flex.flex-col > header",
#             "title": "Article Title"
#         },
#         "description": {
#             "selector": "#main-content > section > div > div.relative.z-3.w-full.lg\:max-w-160 > div:nth-child(2) > div > div.mb-10.max-lg\:mb-6 > div > div.flex.flex-col > div",
#             "title": "Article Description"
#         }
#     },
#     "start_with": None,
#     "split_length": None,
#     "excluded_protocols": ['whatsapp:', 'tel:', 'mailto:'],
#     "max_retries": 5,
#     "base_delay": 1,
#     "concurrent_requests": 10,
#     "connections_per_host": 5,
#     "delay_between_requests": 0.5,
# }
