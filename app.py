from flask import Flask, request, jsonify
from officely_web_scraper.scan import WebScraper
import asyncio

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
async def scrape():
    config = request.json
    scraper = WebScraper(config)
    # Change 'run' to the correct method name from your WebScraper class
    results = await scraper.scrape_website()  
    return jsonify(results)

if __name__ == '__main__':
    app.run()
