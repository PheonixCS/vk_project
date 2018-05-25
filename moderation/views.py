import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from moderation import core


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))

    if received_json_data['type'] == 'confirmation' and core.does_group_exist(received_json_data['group_id']):
        return HttpResponse(core.get_callback_api_key(received_json_data['group_id']))

    if received_json_data['type'] in ('wall_reply_new', 'wall_reply_edit', 'wall_reply_restore'):
        core.handle_comment_event(received_json_data['object'], received_json_data['group_id'])

    return HttpResponse('ok')
