# Project Name

## Description

This project is a Scrapy-based web scraping application named "sreality", designed to scrape real estate listings from the website "www.sreality.cz". It extracts various details about the properties, such as ID, name, price, and location, and stores this information in a PostgreSQL database.

## Requirements
This project requires Python 3.6 or newer. Additionally, it necessitates a PostgreSQL database or Docker for database containerization.

## Installation

To set up the project, follow these steps:

1. Clone the repository to your local machine.
2. Ensure you have Python installed.
3. Install the required Python packages using the command: `pip install -r requirements.txt`.
4. Copy the `.env.example` file, rename it to `.env`, and update the variables with your PostgreSQL database credentials.
5. Optionally, you can use the provided `Dockerfile` and `docker-compose.yml` files to set up a PostgreSQL container with Docker. To do this, run the command: `docker-compose up -d`.

## Usage

To run the scraper:

1. Navigate to the project directory.
2. Run the spider using the command: `scrapy crawl sreality`.

The spider will get sreality data and store them in the PostgreSQL database.

## Contributing

Contributions are welcome. Please follow the standard fork and pull request workflow. Ensure your code adheres to the project's coding standards and include tests where applicable.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any queries or further information, please contact the project maintainer at [insert contact information here].