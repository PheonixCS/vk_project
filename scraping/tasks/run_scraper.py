from celery import shared_task

from scraping.core.scraper import main


@shared_task
def run_scraper():
    main()
