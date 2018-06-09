from django.db import models
from scraping.models import Donor
import datetime


class User(models.Model):
    login = models.CharField(max_length=64, verbose_name='Логин', unique=True)
    password = models.CharField(max_length=64, verbose_name='Пароль')
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    domain_or_id = models.CharField(max_length=128, verbose_name='Domain/id пользователя', blank=True, default='')
    initials = models.CharField(max_length=128, verbose_name='ФИО', blank=True, default='')
    app_id = models.CharField(max_length=256, verbose_name='ID приложения', null=True)

    def save(self, *args, **kwargs):
        if self.domain_or_id.isdigit():
            self.url = 'https://vk.com/id{}'.format(self.domain_or_id)
        elif self.domain_or_id:
            self.url = 'https://vk.com/{}'.format(self.domain_or_id)
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.login, self.initials)


class ServiceToken(models.Model):
    app_service_token = models.CharField(max_length=256, verbose_name='Сервисный ключ приложения', primary_key=True)

    def __str__(self):
        return self.app_service_token


class Group(models.Model):
    domain_or_id = models.CharField(max_length=32, verbose_name='Domain/id группы цели', primary_key=True)
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    name = models.CharField(max_length=128, verbose_name='Название', blank=True, default='')
    group_id = models.IntegerField(null=True)
    is_posting_active = models.BooleanField(default=True, verbose_name='Постинг активен?')
    posting_time = models.TimeField(verbose_name='Время постинга', default=datetime.time(00, 00))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='groups', blank=True, null=True)
    callback_api_token = models.CharField(max_length=128, verbose_name='Ответ для callback api', blank=True, default='')
    donors = models.ManyToManyField(Donor, blank=True)

    def save(self, *args, **kwargs):
        if self.domain_or_id.isdigit():
            self.url = 'https://vk.com/club{}'.format(self.domain_or_id)
        else:
            self.url = 'https://vk.com/{}'.format(self.domain_or_id)
        super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.domain_or_id, self.name)

