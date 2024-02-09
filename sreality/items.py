# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class SrealityItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    labelsAll = scrapy.Field()
    exclusively_at_rk = scrapy.Field()
    category = scrapy.Field()
    has_floor_plan = scrapy.Field()
    locality = scrapy.Field()
    new = scrapy.Field()
    type = scrapy.Field()
    price = scrapy.Field()
    seo_category_main_cb = scrapy.Field()
    seo_category_sub_cb = scrapy.Field()
    seo_category_type_cb = scrapy.Field()
    seo_locality = scrapy.Field()
    price_czk_value_raw = scrapy.Field()
    price_czk_unit = scrapy.Field()
    links_iterator_href = scrapy.Field()
    links_self_href = scrapy.Field()
    links_images = scrapy.Field()
    links_image_middle2 = scrapy.Field()
    gps_lat = scrapy.Field()
    gps_lon = scrapy.Field()
    price_czk_alt_value_raw = scrapy.Field()
    price_czk_alt_unit = scrapy.Field()
    embedded_company_url = scrapy.Field()
    embedded_company_id = scrapy.Field()
    embedded_company_name = scrapy.Field()
    embedded_company_logo_small = scrapy.Field()
