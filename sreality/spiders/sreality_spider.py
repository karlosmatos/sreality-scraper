import scrapy
import json

class SrealitySpider(scrapy.Spider):
    name = "sreality"
    allowed_domains = ["www.sreality.cz"]
    
    # Define the start URL and the query parameters directly in the URL
    start_urls = [
        "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&locality_region_id=10&per_page=999"
    ]

    def parse(self, response):
        # Convert the response data to JSON
        data = json.loads(response.text)
        
        # Save the JSON data to a file
        with open('response.json', 'w') as f:
            json.dump(data, f, indent=4)
        
        # If you want to process the data further, you can iterate over the items
        # For example, to yield each estate's basic info:
        for estate in data.get('_embedded', {}).get('estates', []):
            yield {
                'id': estate.get('hash_id'),
                'name': estate.get('name'),
                'price': estate.get('price_czk'),
                'locality': estate.get('locality_label'),
                'category': estate.get('category_main_cb_label'),
                'url': estate.get('_links', {}).get('self', {}).get('href'),
            }