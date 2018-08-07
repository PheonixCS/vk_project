import json

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moderation import core
from moderation.models import WebhookTransaction


log = logging.getLogger('moderation.views')


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))
    log.debug(received_json_data)

    if received_json_data['type'] == 'confirmation' and core.does_group_exist(received_json_data['group_id']):
        return HttpResponse(core.get_callback_api_key(received_json_data['group_id']))

    WebhookTransaction.objects.create(body=received_json_data)

    return HttpResponse('ok')
