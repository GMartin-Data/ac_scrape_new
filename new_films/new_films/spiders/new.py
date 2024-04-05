import scrapy


class NewSpider(scrapy.Spider):
    name = "new"
    allowed_domains = ["site.com"]
    start_urls = ["https://site.com"]

    def parse(self, response):
        pass
