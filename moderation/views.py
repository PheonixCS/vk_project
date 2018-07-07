import copy
import datetime
import json

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moderation import core
from moderation.models import WebhookTransaction


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))

    # meta = copy.copy(request.META)
    # for k, v in meta.items():
    #     if not isinstance(v, str):
    #         del meta[k]

    WebhookTransaction.objects.create(
        date_generated=datetime.datetime.fromtimestamp(
            received_json_data['timestamp'],
            tz=timezone.get_current_timezone()
        ),
        body=received_json_data
    )

    if received_json_data['type'] == 'confirmation' and core.does_group_exist(received_json_data['group_id']):
        return HttpResponse(core.get_callback_api_key(received_json_data['group_id']))

    return HttpResponse(status=200)
