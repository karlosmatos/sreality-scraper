import scrapy
import json

from sreality.items import SrealityItem

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
        sreality_item = SrealityItem()
        data = json.loads(response.text)
        for estate in data.get('_embedded', {}).get('estates', []):
            sreality_item['id'] = estate.get('hash_id')
            sreality_item['name'] = estate.get('name')
            sreality_item['labelsAll'] = estate.get('labelsAll')
            sreality_item['exclusively_at_rk'] = estate.get('exclusively_at_rk')
            sreality_item['category'] = estate.get('category')
            sreality_item['has_floor_plan'] = estate.get('has_floor_plan')
            sreality_item['locality'] = estate.get('locality')
            sreality_item['new'] = estate.get('new')
            sreality_item['type'] = estate.get('type')
            sreality_item['price'] = estate.get('price')
            sreality_item['seo_category_main_cb'] = estate.get('seo', {}).get('category_main_cb')
            sreality_item['seo_category_sub_cb'] = estate.get('seo', {}).get('category_sub_cb')
            sreality_item['seo_category_type_cb'] = estate.get('seo', {}).get('category_type_cb')
            sreality_item['seo_locality'] = estate.get('seo', {}).get('locality')
            sreality_item['price_czk_value_raw'] = estate.get('price_czk', {}).get('value_raw')
            sreality_item['price_czk_unit'] = estate.get('price_czk', {}).get('unit')
            sreality_item['links_iterator_href'] = estate.get('_links', {}).get('iterator', {}).get('href')
            sreality_item['links_self_href'] = estate.get('_links', {}).get('self', {}).get('href')
            sreality_item['links_images'] = estate.get('_links', {}).get('images')
            sreality_item['gps_lat'] = estate.get('gps', {}).get('lat')
            sreality_item['gps_lon'] = estate.get('gps', {}).get('lon')
            sreality_item['price_czk_alt_value_raw'] = estate.get('price_czk', {}).get('alt', {}).get('value_raw')
            sreality_item['price_czk_alt_unit'] = estate.get('price_czk', {}).get('alt', {}).get('unit')
            sreality_item['embedded_company_url'] = estate.get('_embedded', {}).get('company', {}).get('url')
            sreality_item['embedded_company_id'] = estate.get('_embedded', {}).get('company', {}).get('id')
            sreality_item['embedded_company_name'] = estate.get('_embedded', {}).get('company', {}).get('name')
            sreality_item['embedded_company_logo_small'] = estate.get('_embedded', {}).get('company', {}).get('logo_small')
            yield sreality_item