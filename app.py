from flask import Flask, request, jsonify
from officely_web_scraper.scan import WebScraper
import asyncio
from functools import wraps

app = Flask(__name__)

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
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
