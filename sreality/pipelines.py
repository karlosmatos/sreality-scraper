# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from decouple import config
import psycopg2

class SrealityPipeline:

    def open_spider(self, spider):
        hostname = 'localhost'
        username = config('POSTGRES_USER')
        password = config('POSTGRES_PASSWORD')
        database = config('POSTGRES_DB')

        self.connection = psycopg2.connect(host=hostname, user=username, password=password, dbname=database)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sreality(
                id bigint PRIMARY KEY, 
                name text,
                labelsAll text,
                exclusively_at_rk boolean,
                category text,
                has_floor_plan boolean,
                locality text,
                new boolean,
                type text,
                price text,
                seo_category_main_cb text,
                seo_category_sub_cb text,
                seo_category_type_cb text,
                seo_locality text,
                price_czk_value_raw text,
                price_czk_unit text,
                links_iterator_href text,
                links_self_href text,
                links_images text,
                gps_lat text,
                gps_lon text,
                price_czk_alt_value_raw text,
                price_czk_alt_unit text,
                embedded_company_url text,
                embedded_company_id text,
                embedded_company_name text,
                embedded_company_logo_small text
            )
        """)

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Check if id already exists in the database
        self.cursor.execute("SELECT 1 FROM sreality WHERE id = %s", (adapter.get('id'),))
        if self.cursor.fetchone():
            spider.logger.info(f"Item with id {adapter.get('id')} already exists in the database")
            return item  # Skip this item
    
        columns = ', '.join(adapter.keys())
        values = ', '.join(['%s'] * len(adapter))
        sql = f"INSERT INTO sreality ({columns}) VALUES ({values})"
        
        # Convert all values to string
        values = [str(value) for value in adapter.values()]
        
        try:
            self.cursor.execute(sql, values)
            self.connection.commit()
        except psycopg2.ProgrammingError as e:
            self.connection.rollback()
            spider.logger.error(f"Error processing item: {e}")
            with open('exceptions.log', 'a') as f:
                f.write(f"{e}\n")
        
        return item
