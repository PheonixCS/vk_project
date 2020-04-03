import logging

from celery import shared_task

from posting.core.poster import get_movies_rating_intervals
from scraping.models import Movie, Trailer
from services.youtube.core import download_trailer

log = logging.getLogger('scraping.scheduled')


@shared_task
def download_youtube_trailers():
    log.debug('download_youtube_trailers start analyzing')

    rating_intervals = get_movies_rating_intervals()

    for rating_interval in rating_intervals:
        # check if we got movie with this suitable rating and downloaded trailer
        downloaded_movie = Movie.objects.filter(rating__in=rating_interval,
                                                trailers__status=Trailer.DOWNLOADED_STATUS).first()
        if downloaded_movie:
            continue

        # search for new movie with appropriate interval and new trailer
        movie = Movie.objects.filter(rating__in=rating_interval,
                                     trailers__status=Trailer.NEW_STATUS).first()

        if movie:
            log.debug('work with new movie')
            trailer = movie.trailers.filter(status=Trailer.NEW_STATUS).first()

            if trailer:
                trailer.status = Trailer.PENDING_STATUS
                trailer.save(update_fields=['status'])

                downloaded_trailer_path = download_trailer(trailer.url)

                if downloaded_trailer_path:
                    trailer.status = Trailer.DOWNLOADED_STATUS
                    trailer.file_path = downloaded_trailer_path

                    trailer.save(update_fields=['status', 'file_path'])
                else:
                    trailer.status = Trailer.FAILED_STATUS
                    trailer.save(update_fields=['status'])

        log.debug('finish downloading trailers')
