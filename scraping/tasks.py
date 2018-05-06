#
from celery import task
from scraping.scraper import main


@task
def run_scraper():
    main()
