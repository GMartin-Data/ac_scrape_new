from datetime import date, timedelta
import re

import scrapy

from new_films.items import FilmItem


def convert_dates(date: str) -> str:
    """
    Convenience function to convert dates from Allocine to American format
    """
    date = date.split()
    MONTH_MAPPING = {
        "janvier": "01",
        "février": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12"
    }
    date[1] = MONTH_MAPPING[date[1]]
    date[0] = "0" + date[0] if len(date[0]) == 1 else date[0]
    return "-".join(reversed(date))


class IncomingFilmsSpider(scrapy.Spider):
    name = "incoming_films"

    custom_settings = {
        'ITEM_PIPELINES': {"new_films.pipelines.CleanPipeline": 100}
    }

    def start_requests(self):
        # Getting the release date page
        today = date.today()
        days_until_wednesday = (2 - today.weekday() + 7) % 7
        if days_until_wednesday == 0:
            days_until_wednesday = 7
        next_wednesday = today + timedelta(days=days_until_wednesday)
        next_wed_str = next_wednesday.strftime("%Y-%m-%d")

        releases_url = "https://www.allocine.fr/film/agenda/sem-" + next_wed_str

        yield scrapy.Request(url = releases_url,
                             callback = self.parse_releases_page,
                             meta = {"next_wed_str": next_wed_str})
        

    def parse_releases_page(self, response):
        next_wed_str = response.meta["next_wed_str"]
        # Retrieve incoming films URLs
        url_suffixes = response.css("a.meta-title-link::attr(href)").getall()

        for suffix in url_suffixes:
            film_url = "https://www.allocine.fr" + suffix

            yield scrapy.Request(url = film_url,
                                 callback = self.parse_film_page,
                                 meta = {"next_wed_str": next_wed_str})


    def parse_film_page(self, response):
        next_wed_str = response.meta["next_wed_str"]
        film_info = response.xpath('//div[@class="meta-body-item meta-body-info"]')
        # Filter films not released in theatres
        display = film_info.xpath('.//strong/text()').get().strip()
        if display == "en salle":
            # Filter concerts, festivals and opera
            film_info = film_info.xpath('.//span/text()').getall()
            release_date = film_info.pop(0).strip()
            film_info = set(film_info)
            # We continue only if the sets' intersection is the empty set
            if not(film_info & {"Concert", "Divers", "Opéra"}):
                # Finally, filter films not released on wednesday
                # First, let's check if there's a relaunch_date
                relaunch_date = response.xpath('//div[@class="meta-body-item"]/span[contains(@class, "date")]/text()').get()
                try:
                    relaunch_date = convert_dates(relaunch_date.strip())                    
                except BaseException:
                    pass
                release_date = convert_dates(release_date)
                if next_wed_str in {relaunch_date, release_date}:
                    # WE CAN NOW PROCESS DATA
                    item = FilmItem()
                    item["film_id"] = int(re.search(r"\d+", response.url).group())
                    item["title"] = response.css("div.titlebar-title::text").get()
                    item["img_src"] = response.css("[title^='Bande-'] > img::attr(src)").get()
                    if relaunch_date:
                        item["release"] = relaunch_date
                    else:
                        item["release"] = release_date
                    # Duration & Genres
                    raw_info = response.css('div.meta-body-info ::text').getall()
                    info = [item.strip() for item in raw_info
                            if item not in ('\nen salle\n', '|', '\n', ',\n')]
                    try:
                        item["duration"] = info[1]
                    except IndexError:
                        item["duration"] = None
                    item["genres"] = info[2:]  # A slice never raises an exception

                    item["synopsis"] = response.css("section#synopsis-details div.content-txt p::text").get()

                    # Follow the casting page
                    casting_page_url = f"https://www.allocine.fr/film/fichefilm-{item['film_id']}/casting/"

                    yield scrapy.Request(url = casting_page_url,
                                        callback = self.parse_casting_page,
                                        meta = {"item": item})


    def parse_casting_page(self, response):
        item = response.meta["item"]
        item["director"] = response.css('section.casting-director a::text').getall()
        item["casting"] = response.css('section.casting-actor *.meta-title-link::text').getall()
        societies_fields = response.css('div.gd-col-left div.casting-list-gql')[-1]
        item["societies"] = societies_fields.css("div.md-table-row span.link::text").getall()

        # Don't forget the target! ;)
        item["entries"] = None
        
        yield item
