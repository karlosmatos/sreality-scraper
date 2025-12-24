# Professional pipelines with validation, deduplication, and error handling.

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from decouple import config
from collections import defaultdict
import logging
import csv
import os
from datetime import datetime


class BasePipeline:
    """Base pipeline with common logging and error handling."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_exception(self, exception, item):
        self.logger.error(f"Error processing item: {exception}", exc_info=True)


class ValidationPipeline(BasePipeline):
    """Validate items have required fields before processing."""

    REQUIRED_FIELDS = ['hash_id', 'name']

    def __init__(self):
        super().__init__()
        self.stats = {
            'valid': 0,
            'invalid': 0,
            'missing_fields': defaultdict(int)
        }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        missing = []
        for field in self.REQUIRED_FIELDS:
            if not adapter.get(field):
                missing.append(field)
                self.stats['missing_fields'][field] += 1

        if missing:
            self.stats['invalid'] += 1
            self.logger.warning(
                f"Item {adapter.get('hash_id', 'unknown')} missing fields: {missing}"
            )
            raise DropItem(f"Missing required fields: {missing}")

        self.stats['valid'] += 1
        return item

    def close_spider(self, spider):
        self.logger.info(
            f"Validation: {self.stats['valid']} valid, {self.stats['invalid']} invalid"
        )
        if self.stats['missing_fields']:
            self.logger.warning(f"Missing field counts: {dict(self.stats['missing_fields'])}")


class DeduplicationPipeline(BasePipeline):
    """Remove duplicate items based on hash_id."""

    def __init__(self):
        super().__init__()
        self.seen_ids = set()
        self.duplicates = 0

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        hash_id = adapter.get('hash_id')

        if not hash_id:
            return item

        if hash_id in self.seen_ids:
            self.duplicates += 1
            raise DropItem(f"Duplicate item: {hash_id}")

        self.seen_ids.add(hash_id)
        return item

    def close_spider(self, spider):
        self.logger.info(
            f"Deduplication: {len(self.seen_ids)} unique, {self.duplicates} duplicates removed"
        )


class CountVerificationPipeline(BasePipeline):
    """Verify all expected records were captured."""

    def __init__(self):
        super().__init__()
        self.item_count = 0

    def process_item(self, item, spider):
        self.item_count += 1
        return item

    def close_spider(self, spider):
        expected = getattr(spider, 'total_results', 0)

        if expected:
            if self.item_count < expected:
                self.logger.error(
                    f"RECORD LOSS: Expected {expected}, got {self.item_count} "
                    f"({expected - self.item_count} missing)"
                )
            elif self.item_count == expected:
                self.logger.info(f"SUCCESS: All {self.item_count} records captured")
            else:
                self.logger.info(
                    f"Captured {self.item_count} records (expected {expected})"
                )
        else:
            self.logger.info(f"Processed {self.item_count} items")


class PostgreSQLPipeline(BasePipeline):
    """PostgreSQL pipeline with configurable host and proper error handling."""

    def open_spider(self, spider):
        import psycopg2
        self.psycopg2 = psycopg2

        try:
            self.connection = psycopg2.connect(
                host=config('POSTGRES_HOST', default='localhost'),
                port=config('POSTGRES_PORT', default=5432, cast=int),
                user=config('POSTGRES_USER'),
                password=config('POSTGRES_PASSWORD'),
                dbname=config('POSTGRES_DB')
            )
            self.cursor = self.connection.cursor()
            self._create_table()
            self.logger.info("PostgreSQL connection established")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sreality(
                id VARCHAR(255) PRIMARY KEY,
                hash_id VARCHAR(255) UNIQUE,
                name TEXT,
                labelsAll TEXT,
                exclusively_at_rk BOOLEAN,
                category TEXT,
                has_floor_plan BOOLEAN,
                locality TEXT,
                new BOOLEAN,
                type TEXT,
                price TEXT,
                seo_category_main_cb TEXT,
                seo_category_sub_cb TEXT,
                seo_category_type_cb TEXT,
                seo_locality TEXT,
                price_czk_value_raw INTEGER,
                price_czk_unit TEXT,
                links_iterator_href TEXT,
                links_self_href TEXT,
                links_images TEXT[],
                links_image_middle2 TEXT,
                gps_lat FLOAT,
                gps_lon FLOAT,
                price_czk_alt_value_raw INTEGER,
                price_czk_alt_unit TEXT,
                embedded_company_url TEXT,
                embedded_company_id TEXT,
                embedded_company_name TEXT,
                embedded_company_logo_small TEXT,
                scraped_at TIMESTAMP DEFAULT NOW()
            )
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sreality_hash_id ON sreality(hash_id)
        """)
        self.connection.commit()

    def close_spider(self, spider):
        try:
            self.cursor.close()
            self.connection.close()
            self.logger.info("PostgreSQL connection closed")
        except Exception as e:
            self.logger.error(f"Error closing PostgreSQL connection: {e}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        item_id = adapter.get('id')
        hash_id = adapter.get('hash_id')

        if not item_id:
            self.logger.warning("Item missing 'id' field, skipping")
            return item

        try:
            self.cursor.execute(
                "SELECT 1 FROM sreality WHERE id = %s OR hash_id = %s",
                (item_id, hash_id)
            )
            if self.cursor.fetchone():
                return item

            columns = list(adapter.keys())
            values = [adapter.get(col) for col in columns]
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)

            sql = f"INSERT INTO sreality ({column_names}) VALUES ({placeholders})"
            self.cursor.execute(sql, values)
            self.connection.commit()

        except self.psycopg2.Error as e:
            self.connection.rollback()
            self.process_exception(e, item)

        return item


class MongoDBPipeline(BasePipeline):
    """MongoDB pipeline with proper hash_id handling."""

    def open_spider(self, spider):
        from pymongo import MongoClient, errors
        self.errors = errors

        uri = config('MONGO_URI')
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client['realestatecluster']
            self.collection = self.db['sreality']
            self.collection.create_index('hash_id', unique=True)
            self.logger.info("MongoDB connection established")
        except errors.ServerSelectionTimeoutError as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def close_spider(self, spider):
        try:
            self.client.close()
            self.logger.info("MongoDB connection closed")
        except Exception as e:
            self.logger.error(f"Error closing MongoDB connection: {e}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item).asdict()

        hash_id = adapter.get('hash_id')
        if not hash_id:
            self.logger.warning(f"Item missing hash_id: {adapter.get('id', 'unknown')}")
            return item

        try:
            result = self.collection.update_one(
                {'hash_id': hash_id},
                {'$set': adapter},
                upsert=True
            )
            if result.upserted_id:
                self.logger.debug(f"Inserted: {hash_id}")
            else:
                self.logger.debug(f"Updated: {hash_id}")
        except self.errors.PyMongoError as e:
            self.process_exception(e, item)

        return item


class CSVPipeline(BasePipeline):
    """CSV pipeline with improved field handling and duplicate tracking."""

    def __init__(self):
        super().__init__()
        self.file = None
        self.writer = None
        self.fieldnames = None
        self.seen_fields = set()
        self.items_written = 0

    def open_spider(self, spider):
        output_dir = config('CSV_OUTPUT_DIR', default='data')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = config('CSV_FILENAME', default='') or f'sreality_{timestamp}.csv'
        self.filepath = os.path.join(output_dir, filename)

        self.file = open(self.filepath, 'w', newline='', encoding='utf-8')
        self.logger.info(f"CSV output: {self.filepath}")

    def close_spider(self, spider):
        if self.file:
            self.file.close()
            self.logger.info(f"CSV closed: {self.items_written} items written to {self.filepath}")

        if self.seen_fields and self.fieldnames:
            new_fields = self.seen_fields - set(self.fieldnames)
            if new_fields:
                self.logger.warning(f"Fields discovered after header: {new_fields}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item).asdict()
        flat_item = self._flatten_item(adapter)

        if self.writer is None:
            self.fieldnames = sorted(flat_item.keys())
            self.seen_fields = set(self.fieldnames)
            self.writer = csv.DictWriter(
                self.file,
                fieldnames=self.fieldnames,
                extrasaction='ignore'
            )
            self.writer.writeheader()

        current_fields = set(flat_item.keys())
        new_fields = current_fields - self.seen_fields
        if new_fields:
            self.logger.debug(f"New fields in item: {new_fields}")
            self.seen_fields.update(new_fields)

        try:
            self.writer.writerow(flat_item)
            self.items_written += 1
        except Exception as e:
            self.process_exception(e, item)

        return item

    def _flatten_item(self, item, parent_key='', sep='_'):
        """Flatten nested dictionaries for CSV export."""
        flat = {}
        for key, value in item.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                flat.update(self._flatten_item(value, new_key, sep))
            elif isinstance(value, list):
                flat[new_key] = ', '.join(str(v) for v in value) if value else ''
            else:
                flat[new_key] = value
        return flat
