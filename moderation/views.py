import json

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moderation import core
from vk_scraping_posting.config import callback_api_settings


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))

    if received_json_data['type'] == 'confirmation' and callback_api_settings.get(received_json_data['group_id']):
        return HttpResponse(callback_api_settings.get(received_json_data['group_id']))

    if received_json_data['type'] in ('wall_reply_new', 'wall_reply_edit', 'wall_reply_restore'):
        core.handle_comment_event(received_json_data['object'], received_json_data['group_id'])

    return HttpResponse('ok')
