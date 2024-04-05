import scrapy


class IncomingFilmsSpider(scrapy.Spider):
    name = "incoming_films"

    custom_settings = {
        'ITEM_PIPELINES': {"new_films.pipelines.CleanPipeline": 100}
    }  

    def start_requests(self):
        pass
