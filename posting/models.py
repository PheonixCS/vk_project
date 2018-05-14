from django.db import models
from scraping.models import Donor
import datetime


class User(models.Model):
    login = models.CharField(max_length=64, verbose_name='Логин', unique=True)
    password = models.CharField(max_length=64, verbose_name='Пароль')
    app_id = models.CharField(max_length=256, verbose_name='ID приложения', null=True)
    app_service_token = models.CharField(max_length=256, verbose_name='Сервисный ключ приложения', null=True,
                                         blank=True)

    def __str__(self):
        return self.login


class Group(models.Model):
    domain_or_id = models.CharField(max_length=32, verbose_name='Domain/id группы цели', primary_key=True)
    group_id = models.IntegerField(null=True)
    posting_time = models.TimeField(verbose_name='Время постинга', default=datetime.time(00, 00))
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='groups', blank=True, null=True)
    donors = models.ManyToManyField(Donor, blank=True)
    last_post_time_utc = models.DateTimeField(null=True)

    def __str__(self):
        return self.id
