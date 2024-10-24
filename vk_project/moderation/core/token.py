import requests
from moderation.models import Token
import time
import logging
import hashlib
import string, random
from cryptography.fernet import Fernet
import os

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

crypt=Fernet(key=os.getenv("CRYPT_KEY").encode())
log = logging.getLogger('moderation.core.token')

#Получение авторизационного токена
class GetAuthToken():
    """Позволяет получать актуальный токен"""

    def get_token_by_code(self, code, device_id, redirect_uri, code_verifier, app_id, state):
        """Получение токена по коду авторизации, запись в БД"""  
        #Удаляем все записи о токенах
        Token.objects.all().delete()
        
        #Рандомно генерируется, позднее сверяется
        letters=string.ascii_lowercase+string.digits+string.ascii_uppercase
        # state=''.join(random.choice(letters) for i in range(32))

        request_header={
            "Content-Type":"application/x-www-form-urlencoded"
        }
        request_body={
            "grant_type":"authorization_code",
            "code_verifier":code_verifier,
            "code":code,
            "client_id":app_id,
            "device_id":device_id,
            "state":state,
            "redirect_uri":redirect_uri
        }
        response=requests.post(url = "https://id.vk.com/oauth2/auth", headers=request_header, data=request_body).json()
        
        #Дальше валидация ответа
        try:
            token=Token(
                access_token=crypt.encrypt(str(response['access_token']).encode()).decode(),
                access_token_lifetime=int(time.time()+response["expires_in"]),
                refresh_token=crypt.encrypt(str(response['refresh_token']).encode()).decode(),
                refresh_token_lifetime=int(time.time()+15552000),
                device_id=device_id,
                app_id=app_id
            )
            token.save()
            log.info("added new token info successfully")
            return("ok")
        except Exception as e:
            log.error(f"couldn't get valid response from vk api: {response}, {str(e)}")
            return(f"couldn't get valid response from vk api")


        

    def __get_token_by_refresh(self, token_model:Token):
        """Получение токена по рефреш токену, запись в БД"""

        #Рандомно генерируется, позднее сверяется
        letters=string.ascii_lowercase+string.digits+string.ascii_uppercase
        state=''.join(random.choice(letters) for i in range(32))
        
        device_id=token_model.device_id
        app_id=token_model.app_id
        refresh_token=crypt.decrypt(token_model.refresh_token).decode()
        refresh_token_lifetime=token_model.refresh_token_lifetime
        request_header={
            "Content-Type":"application/x-www-form-urlencoded"
        }
        request_body={
            "grant_type":"refresh_token",
            "refresh_token":refresh_token,
            "client_id":app_id,
            "device_id":device_id,
            "state":state,
            "scope":"wall"
        }
        response=requests.post(url = "https://id.vk.com/oauth2/auth", headers=request_header, data=request_body).json()
        #Дальше валидация ответа
        try:
            if "errors" not in response.keys() and str(response["state"]) == str(state):
                Token.objects.create(
                    access_token=crypt.encrypt(str(response['access_token']).encode()).decode(),
                    access_token_lifetime=int(time.time()+response["expires_in"]) - 100,
                    refresh_token=crypt.encrypt(str(response["refresh_token"]).encode()).decode(),
                    refresh_token_lifetime=refresh_token_lifetime,
                    device_id=device_id,
                    app_id=app_id
                )
                token_model.delete()
                log.info("added new token info successfully")
            else:
                log.error(f"couldn't get valid response from vk api: {response}")
        except:
            log.error(f"couldn't get valid response from vk api: {response}")
        return str(response['access_token'])
    
    def __check_token_lifetime(self, token_model:Token):
        """Проверка сроков жизни токена, если истекли запись в БД"""
        
        is_access_expired=False
        is_refresh_expired=False

        if int(token_model.access_token_lifetime) < int(time.time()):
            is_access_expired=True
        if int(token_model.refresh_token_lifetime) < int(time.time()):
            is_refresh_expired=True
        return [is_access_expired, is_refresh_expired]
    
    def get_actual_token(self, app_id):
        """Отдаёт актуальный access_token"""
        try:
            token_model=Token.objects.get(app_id=app_id)
            lifetimes_check=self.__check_token_lifetime(token_model=token_model)
            if lifetimes_check[1] == True:
                log.error("refresh_token is expired, please, authorize manually")
                return -1
            if lifetimes_check[0] == True:
                return self.__get_token_by_refresh(token_model=token_model)
            else:
                log.info(f"token is actual")
                return crypt.decrypt(token_model.access_token).decode()

        except ObjectDoesNotExist:
            log.error("token with this app_id wasn't found, please, create new manually")
            return -1
        