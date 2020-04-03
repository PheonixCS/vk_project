import os

from celery.schedules import crontab

CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'amqp://localhost:5672')
CELERY_BEAT_SCHEDULE = {
    'scraper_task': {
        'task': 'scraping.tasks.run_scraper.run_scraper',
        'schedule': crontab(minute=0)  # every hour at 0 minute
    },
    'poster_task': {
        'task': 'posting.tasks.examine_groups.examine_groups',
        'schedule': crontab(minute='*')  # every minute
    },
    'pin_best_task': {
        'task': 'posting.tasks.pin_best_post.pin_best_post',
        'schedule': crontab(minute=1, hour='1')  # at 1:01 am UTC (4:01 am by MSK)
    },
    'delete_old_task': {
        'task': 'scraping.tasks.delete_oldest.delete_oldest',
        'schedule': crontab(minute=15, hour=5)  # at 5:15 am UTC (8:15 am by MSK)
    },
    'delete_old_ads': {
        'task': 'posting.tasks.delete_old_ads.delete_old_ads',
        'schedule': crontab(minute=31)  # every hour at 30 minute
    },
    'delete_old_horoscope_records': {
        'task': 'scraping.tasks.delete_old_horoscope_records.delete_old_horoscope_records',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'delete_old_transactions': {
        'task': 'moderation.tasks.delete_old_transactions.delete_old_transactions',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'update_statistics': {
        'task': 'posting.tasks.update_statistics.update_statistics',
        'schedule': crontab(minute=5, hour=1)  # at 1:05 am UTC (4:05 am by MSK)
    },
    'process_moderation_transaction': {
        'task': 'moderation.tasks.process_transactions.process_transactions',
        'schedule': crontab(minute='*')  # every minute
    },
    'ban_donors_admins': {
        'task': 'moderation.tasks.ban_donors_admins',
        'schedule': crontab(minute=0, hour=0)  # at 0:00 am UTC (3:00 am by MSK)
    },
    'sex_statistics_weekly': {
        'task': 'posting.tasks.sex_statistics_weekly.sex_statistics_weekly',
        'schedule': crontab(minute=0, hour=0, day_of_week=0)  # at 0:00 am UTC every sunday (3:00 am by MSK)
    },
    'download_youtube_trailers': {
        'task': 'scraping.tasks.download_youtube_trailers.download_youtube_trailers',
        'schedule': crontab(minute='10, 40')
    },
    'scrap_new_movies': {
        'task': 'scraping.tasks.scrap_new_movies.scrap_new_movies',
        'schedule': crontab(minute=30, hour=0, day_of_week=0)  # at 0:30 am UTC every sunday (3:30 am by MSK)
    },
    'set_donors_average_view': {
        'task': 'scraping.tasks.set_donors_average_view.set_donors_average_view',
        'schedule': crontab(minute=30, hour=1)  # at 1:30 am UTC every day
    },
    'rate_new_posts': {
        'task': 'scraping.tasks.rate_new_posts.rate_new_posts',
        'schedule': crontab(minute='15, 45')  # every hour at 15 and 45 minute
    },
    'parse_horoscopes': {
        'task': 'scraping.tasks.parse_horoscopes.parse_horoscopes',
        'schedule': crontab(minute=55, hour=11)  # at 11:55 am UTC (14:55 am by MSK)
    },
    'delete_old_stat': {
        'task': 'posting.tasks.delete_old_stat.delete_old_stat',
        'schedule': crontab(minute=32, hour=0, day_of_week=0)  # at 0:32 am UTC every sunday (3:32 am by MSK)
    },
    'check_attachments_availability': {
        'task': 'scraping.tasks.check_attachments_availability.check_attachments_availability',
        'schedule': crontab(minute='18, 48')  # every hour at 18 and 48 minute
    },
}
