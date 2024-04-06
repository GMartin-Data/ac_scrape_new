# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from typing import Optional

from itemadapter import ItemAdapter
from loguru import logger


LIST_FIELDS = ("casting", "director", "genres", "nationality")
SET_FIELDS = ("societies", )


def convert_duration(duration: str) -> Optional[int]:
    """Convert a duration string to its minutes counterpart"""
    if duration is None or not duration.endswith("min"):
        return None
    duration = duration.split()
    hours = int(duration[0].replace("h", ""))
    minutes = int(duration[1].replace("min", ""))
    return (60 * hours + minutes)


class CleanPipeline:
    @logger.catch
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in LIST_FIELDS:
            value = adapter.get(field)
            try:
                value = [item.strip() for item in value]
                adapter[field] = "|".join(value)
            except BaseException:
                adapter[field] = None

        for field in SET_FIELDS:
            value = adapter.get(field)
            try:
                value = set(item.strip() for item in value)
                adapter[field] = "|".join(value)
            except BaseException:
                adapter[field] = None

        # Special case of duration
        duration = adapter.get("duration")
        if duration is not None:
            adapter["duration"] = convert_duration(duration)
        else:
            adapter["duration"] = None
   
        return item
