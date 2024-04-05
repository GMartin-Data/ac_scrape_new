# Scraping New Data On Allocine

## Description
Scraper's implementation in order to manage scraping of new data, including:
- Films which are going to be released next week, meaning we have to scrape their **features**, in order to perform the prediction,
- Films which were released last week, meaning we have to scrape their **first week's number of entries** (the target), in order for us to compare it to the corresponding prediction performed last week.

## Timeline
This scraper will be launched with crontab or Airflow.

As number of entries become public on **thursday**, it should be automated to be launched this day.