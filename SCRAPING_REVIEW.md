# Sreality Scraper - Professional Code Review

> **Goal:** Ensure 100% record capture with zero data loss following industry best practices.

---

## Executive Summary

| Metric | Current Status | Target |
|--------|----------------|--------|
| Records Captured | 59,940 | 59,940+ |
| Error Handling | Minimal | Comprehensive |
| Retry Logic | None | Exponential Backoff |
| Data Validation | None | Schema Validation |
| Rate Limiting | None | Auto-throttle |
| Duplicate Detection | Partial | Full Deduplication |

**Current Risk Level:** Medium - Spider works but lacks resilience for edge cases.

---

## Table of Contents

1. [Critical Issues That Can Skip Records](#1-critical-issues-that-can-skip-records)
2. [Professional Scraping Best Practices](#2-professional-scraping-best-practices)
3. [Recommended Architecture](#3-recommended-architecture)
4. [Implementation Guide](#4-implementation-guide)
5. [Monitoring & Validation](#5-monitoring--validation)

---

## 1. Critical Issues That Can Skip Records

### 1.1 Pagination Logic Bug

**Location:** `sreality/spiders/sreality_spider.py:24`

```python
# Current (problematic)
total_pages = result_size // per_page + 2

# Issue: Hardcoded +2 is arbitrary and incorrect
# For 59,940 records at 999/page = 60.06 pages
# Formula yields: 59940 // 999 + 2 = 62 pages (1 extra request)
```

**Risk:** While currently harmless (extra empty request), this logic can fail if:
- API changes pagination behavior
- `result_size` is not evenly divisible
- API returns fewer items mid-scrape

**Professional Fix:**
```python
import math

# Option 1: Ceiling division
total_pages = math.ceil(result_size / per_page)

# Option 2: Dynamic pagination (preferred)
# Continue until response contains fewer items than per_page
def parse_estate(self, response):
    data = json.loads(response.text)
    estates = data.get('_embedded', {}).get('estates', [])

    yield from estates

    # If we got a full page, there might be more
    if len(estates) == self.per_page:
        self.current_page += 1
        yield scrapy.Request(
            f"{self.base_url}?per_page={self.per_page}&page={self.current_page}",
            callback=self.parse_estate
        )
```

### 1.2 No HTTP Error Recovery

**Location:** `sreality/spiders/sreality_spider.py` (missing)

**Current Behavior:**
- No retry on 5xx errors
- No handling for rate limiting (429)
- No timeout configuration
- Network failures cause silent record loss

**Risk:** A single failed request = 999 lost records.

**Professional Fix:**
```python
# In settings.py
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_TIMEOUT = 30

# In spider - add errback handler
def start_requests(self):
    for page in range(1, self.total_pages + 1):
        yield scrapy.Request(
            url=f"{self.base_url}?per_page={self.per_page}&page={page}",
            callback=self.parse_estate,
            errback=self.handle_error,
            meta={'page': page, 'retry_count': 0}
        )

def handle_error(self, failure):
    request = failure.request
    page = request.meta.get('page')
    self.logger.error(f"Failed to fetch page {page}: {failure.value}")

    # Track failed pages for later retry
    self.failed_pages.append(page)
```

### 1.3 JSON Parsing Without Validation

**Location:** `sreality/spiders/sreality_spider.py:21-23, 30-32`

```python
# Current (dangerous)
data = json.loads(response.text)  # Crashes on invalid JSON
result_size = data.get('result_size')  # Returns None silently

# If result_size is None:
# total_pages = None // 999 + 2  # TypeError!
```

**Professional Fix:**
```python
def parse(self, response):
    try:
        data = response.json()  # Scrapy's built-in method
    except json.JSONDecodeError as e:
        self.logger.error(f"Invalid JSON response: {e}")
        return

    result_size = data.get('result_size')
    if not result_size or not isinstance(result_size, int):
        self.logger.error(f"Invalid result_size: {result_size}")
        return

    # Continue with valid data...
```

### 1.4 CSV Pipeline Data Loss

**Location:** `sreality/pipelines.py:147-150`

```python
# Current: Schema locked to first item
if self.writer is None:
    self.fieldnames = list(flat_item.keys())
    self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames,
                                  extrasaction='ignore')  # SILENTLY IGNORES new fields!
```

**Risk:** If first item has 45 fields but later items have 48 fields, 3 fields are silently dropped.

**Professional Fix:**
```python
def open_spider(self, spider):
    # Pre-define all expected fields
    self.fieldnames = [
        'hash_id', 'id', 'name', 'locality', 'price', 'price_czk',
        'category', 'type', 'gps_lat', 'gps_lon', 'attractive_offer',
        # ... all expected fields
    ]
    self.file = open(self.output_path, 'w', newline='', encoding='utf-8')
    self.writer = csv.DictWriter(
        self.file,
        fieldnames=self.fieldnames,
        extrasaction='ignore',
        restval=''  # Empty string for missing fields
    )
    self.writer.writeheader()

def process_item(self, item, spider):
    flat_item = self._flatten_item(item)

    # Log any new fields we haven't seen
    new_fields = set(flat_item.keys()) - set(self.fieldnames)
    if new_fields:
        self.logger.warning(f"New fields detected: {new_fields}")

    self.writer.writerow(flat_item)
    return item
```

### 1.5 MongoDB Pipeline Crash

**Location:** `sreality/pipelines.py:106`

```python
# Current (BROKEN)
result = self.collection.update_one(
    {'hash_id': adapter['hash_id']},  # KeyError if hash_id not in item!
    {'$set': adapter},
    upsert=True
)
```

**Risk:** MongoDB pipeline will crash on first item - `hash_id` not in ItemAdapter.

**Professional Fix:**
```python
def process_item(self, item, spider):
    adapter = ItemAdapter(item)

    # Extract hash_id from raw API response
    hash_id = adapter.get('hash_id')
    if not hash_id:
        self.logger.error(f"Missing hash_id in item: {item.get('id', 'unknown')}")
        return item

    result = self.collection.update_one(
        {'hash_id': hash_id},
        {'$set': dict(adapter)},
        upsert=True
    )
    return item
```

---

## 2. Professional Scraping Best Practices

### 2.1 The "Never Miss a Record" Checklist

| Practice | Status | Priority |
|----------|--------|----------|
| Retry failed requests | Missing | Critical |
| Validate response structure | Missing | Critical |
| Track progress/checkpoints | Missing | High |
| Handle rate limiting | Missing | High |
| Log all errors with context | Partial | High |
| Verify record counts | Missing | High |
| Deduplicate results | Partial | Medium |
| Resume from failure | Missing | Medium |

### 2.2 Request Resilience

```python
# settings.py - Professional configuration
BOT_NAME = 'sreality'

# Retry Configuration
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 520, 521, 522, 523, 524]
RETRY_PRIORITY_ADJUST = -1

# Timeout Configuration
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 0.5  # 500ms between requests

# Concurrent Requests (be polite)
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0

# Error Handling
HTTPERROR_ALLOWED_CODES = []  # Let Scrapy handle all HTTP errors
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'
```

### 2.3 Data Validation Pipeline

```python
# pipelines.py - Add validation pipeline
class ValidationPipeline:
    """Validate items before storage to prevent data corruption."""

    REQUIRED_FIELDS = ['hash_id', 'id', 'name', 'price']

    def __init__(self):
        self.stats = {
            'valid': 0,
            'invalid': 0,
            'missing_fields': defaultdict(int)
        }

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Check required fields
        missing = []
        for field in self.REQUIRED_FIELDS:
            if not adapter.get(field):
                missing.append(field)
                self.stats['missing_fields'][field] += 1

        if missing:
            self.stats['invalid'] += 1
            spider.logger.warning(
                f"Item {adapter.get('id', 'unknown')} missing fields: {missing}"
            )
            raise DropItem(f"Missing required fields: {missing}")

        self.stats['valid'] += 1
        return item

    def close_spider(self, spider):
        spider.logger.info(f"Validation stats: {dict(self.stats)}")
```

### 2.4 Progress Tracking & Checkpointing

```python
# spider with checkpoint support
class SrealitySpider(scrapy.Spider):
    name = 'sreality'

    def __init__(self, resume=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_file = 'checkpoint.json'
        self.processed_pages = set()
        self.failed_pages = []

        if resume and os.path.exists(self.checkpoint_file):
            self._load_checkpoint()

    def _load_checkpoint(self):
        with open(self.checkpoint_file, 'r') as f:
            data = json.load(f)
            self.processed_pages = set(data.get('processed_pages', []))
            self.failed_pages = data.get('failed_pages', [])
            self.logger.info(f"Resumed from checkpoint: {len(self.processed_pages)} pages done")

    def _save_checkpoint(self):
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                'processed_pages': list(self.processed_pages),
                'failed_pages': self.failed_pages,
                'timestamp': datetime.now().isoformat()
            }, f)

    def parse_estate(self, response):
        page = response.meta.get('page')
        data = response.json()
        estates = data.get('_embedded', {}).get('estates', [])

        yield from estates

        # Mark page as processed
        self.processed_pages.add(page)

        # Save checkpoint every 10 pages
        if len(self.processed_pages) % 10 == 0:
            self._save_checkpoint()

    def closed(self, reason):
        self._save_checkpoint()
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Processed: {len(self.processed_pages)} pages")
        self.logger.info(f"Failed: {len(self.failed_pages)} pages")
```

### 2.5 Record Count Verification

```python
# pipelines.py - Add count verification
class CountVerificationPipeline:
    """Verify we captured all expected records."""

    def open_spider(self, spider):
        self.item_count = 0
        self.expected_count = None

    def process_item(self, item, spider):
        self.item_count += 1

        # Capture expected count from first response
        if self.expected_count is None:
            self.expected_count = getattr(spider, 'total_results', None)

        return item

    def close_spider(self, spider):
        if self.expected_count:
            if self.item_count < self.expected_count:
                spider.logger.error(
                    f"RECORD LOSS DETECTED: Expected {self.expected_count}, "
                    f"got {self.item_count} ({self.expected_count - self.item_count} missing)"
                )
            elif self.item_count == self.expected_count:
                spider.logger.info(
                    f"SUCCESS: All {self.item_count} records captured"
                )
            else:
                spider.logger.warning(
                    f"More records than expected: {self.item_count} vs {self.expected_count}"
                )
```

---

## 3. Recommended Architecture

### 3.1 Pipeline Order

```python
# settings.py
ITEM_PIPELINES = {
    'sreality.pipelines.ValidationPipeline': 100,      # First: validate
    'sreality.pipelines.DeduplicationPipeline': 200,   # Second: dedupe
    'sreality.pipelines.CountVerificationPipeline': 300,  # Third: count
    'sreality.pipelines.CSVPipeline': 400,             # Fourth: export
}
```

### 3.2 Improved Spider Structure

```python
# sreality/spiders/sreality_spider.py
import scrapy
import json
import math
from datetime import datetime

class SrealitySpider(scrapy.Spider):
    name = 'sreality'
    allowed_domains = ['sreality.cz']

    # Configuration
    base_url = 'https://www.sreality.cz/api/cs/v2/estates'
    per_page = 999

    # Statistics
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'RETRY_TIMES': 5,
        'DOWNLOAD_TIMEOUT': 30,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_results = 0
        self.pages_fetched = 0
        self.items_yielded = 0
        self.failed_requests = []

    def start_requests(self):
        """Initial request to get total count."""
        yield scrapy.Request(
            url=f"{self.base_url}?per_page=1&page=1",
            callback=self.parse_count,
            errback=self.handle_error,
            meta={'dont_retry': False}
        )

    def parse_count(self, response):
        """Parse total count and generate all page requests."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error("Failed to parse initial response")
            return

        self.total_results = data.get('result_size', 0)
        if not self.total_results:
            self.logger.error("No results found")
            return

        total_pages = math.ceil(self.total_results / self.per_page)
        self.logger.info(f"Total: {self.total_results} records across {total_pages} pages")

        # Generate all page requests
        for page in range(1, total_pages + 1):
            yield scrapy.Request(
                url=f"{self.base_url}?per_page={self.per_page}&page={page}",
                callback=self.parse_estate,
                errback=self.handle_error,
                meta={'page': page}
            )

    def parse_estate(self, response):
        """Parse estate listings from a page."""
        page = response.meta.get('page', 'unknown')

        try:
            data = response.json()
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON on page {page}")
            self.failed_requests.append(page)
            return

        estates = data.get('_embedded', {}).get('estates', [])

        if not estates:
            self.logger.warning(f"No estates on page {page}")

        for estate in estates:
            # Add metadata
            estate['_scraped_at'] = datetime.utcnow().isoformat()
            estate['_page'] = page
            self.items_yielded += 1
            yield estate

        self.pages_fetched += 1
        self.logger.debug(f"Page {page}: {len(estates)} items (total: {self.items_yielded})")

    def handle_error(self, failure):
        """Handle request failures."""
        request = failure.request
        page = request.meta.get('page', 'unknown')

        self.logger.error(f"Request failed for page {page}: {failure.value}")
        self.failed_requests.append(page)

    def closed(self, reason):
        """Log final statistics."""
        self.logger.info("=" * 50)
        self.logger.info("SCRAPING COMPLETE")
        self.logger.info(f"Expected: {self.total_results} records")
        self.logger.info(f"Yielded:  {self.items_yielded} records")
        self.logger.info(f"Pages:    {self.pages_fetched}")
        self.logger.info(f"Failed:   {len(self.failed_requests)} requests")

        if self.failed_requests:
            self.logger.warning(f"Failed pages: {self.failed_requests}")

        if self.items_yielded < self.total_results:
            missing = self.total_results - self.items_yielded
            self.logger.error(f"MISSING {missing} RECORDS!")

        self.logger.info("=" * 50)
```

### 3.3 Deduplication Pipeline

```python
class DeduplicationPipeline:
    """Prevent duplicate records using hash_id."""

    def open_spider(self, spider):
        self.seen_ids = set()
        self.duplicates = 0

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        hash_id = adapter.get('hash_id')

        if hash_id in self.seen_ids:
            self.duplicates += 1
            raise DropItem(f"Duplicate item: {hash_id}")

        self.seen_ids.add(hash_id)
        return item

    def close_spider(self, spider):
        spider.logger.info(f"Dedupe: {self.duplicates} duplicates removed")
```

---

## 4. Implementation Guide

### 4.1 Quick Fixes (Apply Now)

```bash
# 1. Fix pagination in spider
sed -i '' 's/per_page + 2/per_page) + 1/g' sreality/spiders/sreality_spider.py

# 2. Add retry settings
cat >> sreality/settings.py << 'EOF'

# Retry Configuration
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY = 0.25
EOF
```

### 4.2 Settings Configuration

Add to `sreality/settings.py`:

```python
# ============================================
# PROFESSIONAL SCRAPING CONFIGURATION
# ============================================

# Retry Configuration
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 520, 521, 522, 523, 524]

# Timeout Configuration
DOWNLOAD_TIMEOUT = 30

# Rate Limiting (be a good citizen)
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Auto-throttle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Stats
STATS_DUMP = True
```

### 4.3 Environment Variables

Update `.env.example`:

```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=sreality

# MongoDB
MONGO_URI=

# Scraper Configuration
SCRAPER_PER_PAGE=999
SCRAPER_DOWNLOAD_DELAY=0.25
SCRAPER_CONCURRENT_REQUESTS=8

# Output Configuration
CSV_OUTPUT_DIR=data
```

---

## 5. Monitoring & Validation

### 5.1 Post-Scrape Validation Script

```python
#!/usr/bin/env python3
"""validate_scrape.py - Verify scraping completeness."""

import csv
import json
import requests
from collections import Counter

def validate_csv(filepath):
    """Validate CSV output file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check for duplicates
    hash_ids = [r.get('hash_id') for r in rows]
    duplicates = [id for id, count in Counter(hash_ids).items() if count > 1]

    # Check for missing required fields
    required = ['hash_id', 'id', 'name', 'price']
    missing = []
    for i, row in enumerate(rows):
        for field in required:
            if not row.get(field):
                missing.append((i, field))

    print(f"Total records: {len(rows)}")
    print(f"Unique hash_ids: {len(set(hash_ids))}")
    print(f"Duplicates: {len(duplicates)}")
    print(f"Missing required fields: {len(missing)}")

    if duplicates:
        print(f"  Duplicate IDs: {duplicates[:10]}...")
    if missing:
        print(f"  Missing fields sample: {missing[:10]}...")

    return len(rows), len(duplicates), len(missing)

def get_api_count():
    """Get current record count from API."""
    url = "https://www.sreality.cz/api/cs/v2/estates?per_page=1&page=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data.get('result_size', 0)

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_scrape.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    api_count = get_api_count()
    csv_count, dups, missing = validate_csv(csv_file)

    print(f"\n{'='*50}")
    print(f"API reports: {api_count} records")
    print(f"CSV contains: {csv_count} records")
    print(f"Difference: {api_count - csv_count}")

    if csv_count >= api_count:
        print("\n SUCCESS: All records captured!")
    else:
        print(f"\n WARNING: {api_count - csv_count} records may be missing")
```

### 5.2 Logging Best Practices

```python
# In spider - use structured logging
import logging

class SrealitySpider(scrapy.Spider):
    def __init__(self):
        self.logger.setLevel(logging.INFO)

    def parse_estate(self, response):
        page = response.meta.get('page')

        # Structured log with context
        self.logger.info(
            "Page processed",
            extra={
                'page': page,
                'items': len(estates),
                'total_so_far': self.items_yielded
            }
        )
```

---

## Summary: Zero Record Loss Checklist

Before each scrape:
- [ ] Verify API is accessible
- [ ] Check `result_size` matches expectations
- [ ] Ensure output directory exists and is writable

During scrape:
- [ ] Monitor for retry warnings in logs
- [ ] Check memory usage doesn't grow unbounded
- [ ] Verify items are being written to output

After scrape:
- [ ] Compare output count vs API `result_size`
- [ ] Check for duplicates in output
- [ ] Validate required fields are populated
- [ ] Archive output with timestamp

---

*Generated: 2024-12-24*
*Review Version: 1.0*
