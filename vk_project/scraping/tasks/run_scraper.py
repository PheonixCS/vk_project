from celery import shared_task

from scraping.core.scraper import main_scraper


@shared_task
def run_scraper():
    main_scraper()
