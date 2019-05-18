# functions to store scraping statistics
from scraping.models import ScrapingHistory


def save_filter_stats(group, filter_name, filtered_number):
    obj = ScrapingHistory.objects.create(
        group=group,
        filter_name=filter_name,
        filtered_number=filtered_number
    )
    return obj

