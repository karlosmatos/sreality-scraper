# Sreality Scraper

## Description

This project is a Scrapy-based web scraping application that extracts real estate listings from the sreality.cz API. The spider uses the public API endpoint (`https://www.sreality.cz/api/cs/v2/estates`) to fetch property data and stores it in a database.

The scraper extracts comprehensive property information including:
- Basic details: ID, name, category, type, locality
- Pricing: price, price_czk_value_raw, price_czk_unit, price_czk_alt_value_raw, price_czk_alt_unit
- Location: GPS coordinates (latitude/longitude), seo_locality
- Media: image links, floor plan availability
- Company information: embedded company details (URL, ID, name, logo)
- SEO metadata: category and type classifications
- Additional metadata: labels, exclusivity flags, new property indicators

## Requirements

- Python 3.6 or newer
- For database storage: MongoDB or PostgreSQL (optional - CSV export works without any database)
- Docker (optional, for database containerization)

## Installation

To set up the project, follow these steps:

1. Clone the repository to your local machine.
2. Ensure you have Python installed.
3. Install the required Python packages using the command: `pip install -r requirements.txt`.
4. (Optional) Create a `.env` file in the project root if you want to customize output or use database pipelines:
   - `CSV_OUTPUT_DIR`: Directory for CSV output (default: `data`)
   - `CSV_FILENAME`: Custom CSV filename (default: `sreality_<timestamp>.csv`)
   - `MONGO_URI`: MongoDB connection string (if using MongoDB pipeline)
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: PostgreSQL credentials (if using PostgreSQL pipeline)
5. Optionally, you can use the provided `Dockerfile` and `docker-compose.yml` files to set up a PostgreSQL container with Docker. To do this, run the command: `docker-compose up -d`.

## Usage

To run the scraper:

1. Navigate to the project directory.
2. Run the spider using the command: `scrapy crawl sreality`.

The spider will fetch sreality data from the API and export it to the configured output (CSV by default). The spider automatically paginates through all available listings.

### Output Configuration

The project includes three output pipelines:
- **CSVPipeline** (currently active): Exports data to `data/sreality_<timestamp>.csv`. Configure output directory with `CSV_OUTPUT_DIR` and filename with `CSV_FILENAME` env vars
- **MongoDBPipeline**: Stores data in MongoDB collection `sreality` in database `realestatecluster`
- **PostgreSQLPipeline**: Stores data in PostgreSQL table `sreality`

To switch between pipelines, modify the `ITEM_PIPELINES` setting in `sreality/settings.py`.

## Contributing

Contributions are welcome. Please follow the standard fork and pull request workflow.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any queries or further information, please contact the project maintainer at [me@karelmaly.com].
