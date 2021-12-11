# functions to store scraping statistics
from scraping.models import ScrapingHistory


def save_filter_stats(group_donor, filter_name, filtered_number):
    obj = ScrapingHistory.objects.create(
        group=group_donor,
        filter_name=filter_name,
        filtered_number=filtered_number
    )
    return obj

