# Scrapy settings for sreality project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "sreality"

SPIDER_MODULES = ["sreality.spiders"]
NEWSPIDER_MODULE = "sreality.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "sreality (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# ============================================
# RETRY CONFIGURATION (Critical for data completeness)
# ============================================
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 520, 521, 522, 523, 524]
RETRY_PRIORITY_ADJUST = -1

# ============================================
# TIMEOUT CONFIGURATION
# ============================================
DOWNLOAD_TIMEOUT = 30

# ============================================
# RATE LIMITING (Polite scraping)
# ============================================
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en,cs;q=0.9',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Referer': 'https://www.sreality.cz/hledani/prodej/byty/praha',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-gpc': '1',
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "sreality.middlewares.SrealitySpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "sreality.middlewares.SrealityDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# Pipeline order: Validate -> Dedupe -> Count -> Export
# Available pipelines:
#   - ValidationPipeline: Validates required fields exist
#   - DeduplicationPipeline: Removes duplicate items by hash_id
#   - CountVerificationPipeline: Verifies all records were captured
#   - CSVPipeline: Export to CSV file (default: data/sreality_<timestamp>.csv)
#   - MongoDBPipeline: Store in MongoDB (requires MONGO_URI in .env)
#   - PostgreSQLPipeline: Store in PostgreSQL (requires POSTGRES_* in .env)
ITEM_PIPELINES = {
    "sreality.pipelines.ValidationPipeline": 100,
    "sreality.pipelines.DeduplicationPipeline": 200,
    "sreality.pipelines.CountVerificationPipeline": 300,
    "sreality.pipelines.CSVPipeline": 400,
}

# ============================================
# AUTO-THROTTLE (Adaptive rate limiting)
# ============================================
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
STATS_DUMP = True

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
