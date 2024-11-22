from flask import Flask, request, jsonify
from officely_web_scraper.scan import WebScraper
import asyncio

app = Flask(__name__)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/scrape', methods=['POST'])
def scrape():
    config = request.get_json()
    scraper = WebScraper(config)
    results = run_async(scraper.scan_website(config['domain']))
    return jsonify(results)
