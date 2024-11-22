from flask import Flask, request, jsonify
from officely_web_scraper.scan import WebScraper
import asyncio
from quart import Quart

app = Quart(__name__)

@app.route('/scrape', methods=['POST'])
async def scrape():
    config = await request.get_json()
    scraper = WebScraper(config)
    async with scraper as s:
        results = await s.scan_website(config['domain'])
    return jsonify(results)

if __name__ == '__main__':
    app.run()
