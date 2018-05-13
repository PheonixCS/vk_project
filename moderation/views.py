import json

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moderation import core


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))

    # Добавить проверку id группы (словарь в конфиг-файле?)
    if received_json_data['type'] == 'confirmation' and received_json_data['group_id'] == '':
        # Строка, которую должен вернуть сервер
        return HttpResponse('')

    if received_json_data['type'] in ('wall_reply_new', 'wall_reply_edit', 'wall_reply_restore'):
        core.handle_comment_event(received_json_data['object'], received_json_data['group_id'])

    return HttpResponse('ok')
