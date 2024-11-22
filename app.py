from flask import Flask, request, jsonify
from officely_web_scraper.scan import WebScraper
import asyncio
from functools import wraps

app = Flask(__name__)

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapped

@app.route('/scrape', methods=['POST'])
@async_route
async def scrape():
    config = request.json
    scraper = WebScraper(config)
    results = await scraper.run()
    return jsonify(results)

if __name__ == '__main__':
    app.run()
