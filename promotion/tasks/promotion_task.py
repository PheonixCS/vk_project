import logging

from celery import shared_task

from promotion.models.promotion_task import PromotionTask
from services.promotion_z1y1x1.api import create_new_task

log = logging.getLogger(__name__)


@shared_task
def add_promotion_task(post_url):
    log.debug(f'try new task for {post_url}')
    task_id = create_new_task(post_url)

    if not task_id:
        log.error('No task id')
        return

    PromotionTask.objects.create(
        external_id=task_id,
        status=PromotionTask.SENT
    )
    log.debug(f'promotion task for post {post_url}')
