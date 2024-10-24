import json

import logging

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from moderation.core.helpers import does_group_exist, get_callback_api_key
from moderation.models import WebhookTransaction, AuthorizationTransactions, Token

import string,random, pkce

from moderation.core.token import GetAuthToken

log = logging.getLogger('moderation.views')


@csrf_exempt
@require_POST
def webhook(request):
    received_json_data = json.loads(request.body.decode("utf-8"))
    log.debug(received_json_data)

    if received_json_data['type'] == 'confirmation' and does_group_exist(received_json_data['group_id']):
        return HttpResponse(get_callback_api_key(received_json_data['group_id']))

    WebhookTransaction.objects.create(body=received_json_data)

    return HttpResponse('ok')

@csrf_exempt
def auth(request):
    received_data=request.GET
    if "code" not in received_data.keys():
        #Рандомно генерируется, позднее сверяется
        try:
            letters=string.ascii_lowercase+string.digits+string.ascii_uppercase
            state=''.join(random.choice(letters) for i in range(32))

            code_verifier = pkce.generate_code_verifier(length=128)
            code_challenge = pkce.get_code_challenge(code_verifier)
            redirect_uri="https://ahuyang.ru/moderation/auth"
            path_to="https://id.vk.com/authorize?"
            args=f"response_type=code&client_id={received_data['app_id']}&code_challenge={code_challenge}&code_challenge_method=S256&redirect_uri={redirect_uri}&state={state}&scope=wall"
            full_path=path_to+args

            AuthorizationTransactions.objects.create(state=state, code_verifier=code_verifier, app_id=received_data["app_id"])
            return HttpResponseRedirect(full_path)
        except Exception as e:
            return HttpResponse("data parsing error, check arguments in URL and try again. error text: "+str(e))
    else:
        try:
            auth_tranzac_model=AuthorizationTransactions.objects.get(state=received_data["state"])
            tokenAuthObj=GetAuthToken()
            result=tokenAuthObj.get_token_by_code(code=received_data["code"],
                                        device_id=received_data["device_id"],
                                        redirect_uri="https://ahuyang.ru/moderation/auth",
                                        code_verifier=auth_tranzac_model.code_verifier,
                                        app_id=auth_tranzac_model.app_id,
                                        state=auth_tranzac_model.state)
            return HttpResponse(str(result))
        except ObjectDoesNotExist:
            return Http404
        except MultipleObjectsReturned:
            AuthorizationTransactions.objects.all().delete()
            return HttpResponseServerError
        except Exception as e:
            return HttpResponse("error has arised: "+str(e))