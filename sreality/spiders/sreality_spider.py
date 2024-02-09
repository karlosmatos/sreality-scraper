import scrapy
import json

class SrealitySpider(scrapy.Spider):
    name = "sreality"
    allowed_domains = ["www.sreality.cz"]
    base_url = "https://www.sreality.cz/api/cs/v2/estates"
    per_page = 999  # Number of items per page

    def start_requests(self):
        url = f"{self.base_url}?per_page={self.per_page}"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        result_size = data.get('result_size')
        total_pages = result_size // self.per_page + 2

        for page in range(1, total_pages):
            url = f"{self.base_url}?per_page={self.per_page}&page={page}"
            yield scrapy.Request(url, callback=self.parse_estate)

    def parse_estate(self, response):
        data = json.loads(response.text)
        yield from data.get('_embedded', {}).get('estates', [])