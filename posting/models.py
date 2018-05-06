from django.db import models
from scraping.models import Donor
import datetime


class User(models.Model):
    login = models.CharField(max_length=64, verbose_name='Логин', unique=True)
    password = models.CharField(max_length=64, verbose_name='Пароль')
    app_service_token = models.CharField(max_length=64, verbose_name='Сервисный ключ приложения', null=True, blank=True)


class Group(models.Model):
    id = models.CharField(max_length=32, verbose_name='Domain/id группы цели', primary_key=True)
    posting_time = models.TimeField(verbose_name='Время постинга', default=datetime.time(00, 00))
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True)
    donors = models.ManyToManyField(Donor, blank=True)
