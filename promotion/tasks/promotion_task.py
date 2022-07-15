import logging

from celery import shared_task

from promotion.models.promotion_task import PromotionTask
from services.promotion_z1y1x1.api import create_new_task, check_task_status

log = logging.getLogger(__name__)


@shared_task
def add_promotion_task(post_url):
    log.debug(f'try new task for {post_url}')
    creation_res = create_new_task(post_url)
    task_id = creation_res.get('task_id')

    if not task_id:
        log.error('No task')
        return

    obj = PromotionTask.objects.create(
        external_id=task_id,
        status=PromotionTask.SENT
    )
    log.debug(f'promotion task for post {post_url}')

    status_res = check_task_status(task_id)

    obj.status_result = str(status_res)
    obj.save()
