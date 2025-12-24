# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scrapy-based web scraper that extracts Czech real estate listings from the sreality.cz public API and stores them in CSV, MongoDB, or PostgreSQL.

## Commands

```bash
# Run the scraper
scrapy crawl sreality

# Start PostgreSQL container (if using PostgreSQL pipeline)
docker-compose up -d
```

## Architecture

### Data Flow
1. **Spider** (`sreality/spiders/sreality_spider.py`) - Fetches from `https://www.sreality.cz/api/cs/v2/estates` API, paginates through results (999 items/page), yields raw estate dicts directly from API response
2. **Pipeline** (`sreality/pipelines.py`) - Processes items and exports to configured output. CSVPipeline is active by default
3. **Items** (`sreality/items.py`) - Defines SrealityItem schema (not currently used - spider yields raw dicts)

### Output Configuration
- **CSV** (active): Exports to `data/sreality_<timestamp>.csv`. Optionally configure `CSV_OUTPUT_DIR` and `CSV_FILENAME` env vars
- **MongoDB**: Uses `MONGO_URI` env var, stores in `realestatecluster.sreality` collection, upserts by `hash_id`
- **PostgreSQL**: Uses `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` env vars, checks for duplicates by `id`

To switch pipelines, modify `ITEM_PIPELINES` in `sreality/settings.py`.

### Environment Setup
Copy `.env.example` to `.env` and configure database credentials.
