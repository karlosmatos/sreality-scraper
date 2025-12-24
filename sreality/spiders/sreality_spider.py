import scrapy
import json
import math
from datetime import datetime


class SrealitySpider(scrapy.Spider):
    name = "sreality"
    allowed_domains = ["www.sreality.cz"]
    base_url = "https://www.sreality.cz/api/cs/v2/estates"
    per_page = 999

    # Category filters to bypass the ~60 page API limit
    # Each category has fewer results, allowing full pagination
    CATEGORIES = [
        {"name": "Byty - Prodej", "category_main_cb": 1, "category_type_cb": 1},
        {"name": "Byty - Pronájem", "category_main_cb": 1, "category_type_cb": 2},
        {"name": "Domy - Prodej", "category_main_cb": 2, "category_type_cb": 1},
        {"name": "Domy - Pronájem", "category_main_cb": 2, "category_type_cb": 2},
        {"name": "Pozemky - Prodej", "category_main_cb": 3, "category_type_cb": 1},
        {"name": "Pozemky - Pronájem", "category_main_cb": 3, "category_type_cb": 2},
        {"name": "Komerční - Prodej", "category_main_cb": 4, "category_type_cb": 1},
        {"name": "Komerční - Pronájem", "category_main_cb": 4, "category_type_cb": 2},
    ]

    custom_settings = {
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 30,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_results = 0
        self.pages_fetched = 0
        self.items_yielded = 0
        self.failed_requests = []
        self.category_stats = {}

    def start_requests(self):
        """Generate initial requests for each category to get counts."""
        for cat in self.CATEGORIES:
            params = f"category_main_cb={cat['category_main_cb']}&category_type_cb={cat['category_type_cb']}"
            yield scrapy.Request(
                url=f"{self.base_url}?{params}&per_page=1&page=1",
                callback=self.parse_category_count,
                errback=self.handle_error,
                meta={
                    'category': cat,
                    'params': params
                }
            )

    def parse_category_count(self, response):
        """Parse category count and generate page requests for that category."""
        category = response.meta['category']
        params = response.meta['params']

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse response for {category['name']}: {e}")
            return

        result_size = data.get('result_size', 0)
        if not result_size:
            self.logger.info(f"No results for {category['name']}")
            return

        total_pages = math.ceil(result_size / self.per_page)
        self.total_results += result_size
        self.category_stats[category['name']] = {
            'expected': result_size,
            'fetched': 0
        }

        self.logger.info(
            f"Category '{category['name']}': {result_size:,} records across {total_pages} pages"
        )

        for page in range(1, total_pages + 1):
            yield scrapy.Request(
                url=f"{self.base_url}?{params}&per_page={self.per_page}&page={page}",
                callback=self.parse_estate,
                errback=self.handle_error,
                meta={
                    'page': page,
                    'category': category['name'],
                    'params': params
                }
            )

    def parse_estate(self, response):
        """Parse estate listings from a page."""
        page = response.meta.get('page', 'unknown')
        category = response.meta.get('category', 'unknown')

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON on {category} page {page}: {e}")
            self.failed_requests.append(f"{category}:{page}")
            return

        estates = data.get('_embedded', {}).get('estates', [])

        if not estates:
            self.logger.warning(f"No estates on {category} page {page}")

        for estate in estates:
            estate['_scraped_at'] = datetime.utcnow().isoformat()
            estate['_page'] = page
            estate['_category'] = category
            self.items_yielded += 1

            if category in self.category_stats:
                self.category_stats[category]['fetched'] += 1

            yield estate

        self.pages_fetched += 1

        if self.pages_fetched % 20 == 0:
            self.logger.info(
                f"Progress: {self.pages_fetched} pages, {self.items_yielded:,} items"
            )

    def handle_error(self, failure):
        """Handle request failures."""
        request = failure.request
        page = request.meta.get('page', 'initial')
        category = request.meta.get('category', 'unknown')

        self.logger.error(f"Request failed for {category} page {page}: {failure.value}")
        self.failed_requests.append(f"{category}:{page}")

    def closed(self, reason):
        """Log final statistics."""
        self.logger.info("=" * 60)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info("=" * 60)

        self.logger.info("Category breakdown:")
        for cat_name, stats in self.category_stats.items():
            status = "OK" if stats['fetched'] >= stats['expected'] else "INCOMPLETE"
            self.logger.info(
                f"  {cat_name}: {stats['fetched']:,}/{stats['expected']:,} [{status}]"
            )

        self.logger.info("-" * 60)
        self.logger.info(f"Total expected: {self.total_results:,} records")
        self.logger.info(f"Total yielded:  {self.items_yielded:,} records")
        self.logger.info(f"Pages fetched:  {self.pages_fetched}")
        self.logger.info(f"Failed requests: {len(self.failed_requests)}")

        if self.failed_requests:
            self.logger.warning(f"Failed: {self.failed_requests[:20]}...")

        if self.items_yielded >= self.total_results:
            self.logger.info("SUCCESS: All records captured!")
        else:
            missing = self.total_results - self.items_yielded
            self.logger.error(f"MISSING {missing:,} RECORDS!")

        self.logger.info("=" * 60)
