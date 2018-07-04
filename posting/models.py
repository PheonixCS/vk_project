import datetime

from django.db import models


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

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'


class ServiceToken(models.Model):
    app_service_token = models.CharField(max_length=256, verbose_name='Сервисный ключ приложения', primary_key=True)

    def __str__(self):
        return self.app_service_token

    class Meta:
        verbose_name = 'Сервисный токен'
        verbose_name_plural = 'Сервисные токены'


class Group(models.Model):
    domain_or_id = models.CharField(max_length=32, verbose_name='Domain/id группы цели', primary_key=True)
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    statistic_url = models.URLField(max_length=256, verbose_name='Ссылка на статистику', blank=True, default='')
    name = models.CharField(max_length=128, verbose_name='Название', blank=True, default='')
    group_id = models.IntegerField(null=True)
    is_posting_active = models.BooleanField(default=True, verbose_name='Постинг активен?')
    is_horoscopes = models.BooleanField(default=False, verbose_name='Постинг гороскопов задействован?')
    is_pin_enabled = models.BooleanField(default=True, verbose_name='Закреплять лучшие посты?')
    is_text_filling_enabled = models.BooleanField(default=False, verbose_name='Переносить текст на картинку?')
    RGB_image_tone = models.CharField(max_length=15, blank=True, default='',
                                      verbose_name='Применять RBG тон к изображениям (R G B factor)')
    posting_time = models.TimeField(verbose_name='Время постинга', default=datetime.time(00, 00))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='groups', blank=True, null=True)
    callback_api_token = models.CharField(max_length=128, verbose_name='Ответ для callback api', blank=True, default='')
    donors = models.ManyToManyField('scraping.Donor', blank=True)

    number_of_subscribers = models.IntegerField(null=True)
    subscribers_growth = models.IntegerField(null=True)
    number_of_post_yesterday = models.IntegerField(null=True)
    number_of_ad_posts_yesterday = models.IntegerField(null=True)
    statistics_last_update_date = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        if self.domain_or_id.isdigit():
            self.url = 'https://vk.com/club{}'.format(self.domain_or_id)
            self.statistic_url = 'https://vk.com/stats?gid={group_id_int}'.format(group_id_int=self.domain_or_id)
        else:
            self.url = 'https://vk.com/{}'.format(self.domain_or_id)
            if self.group_id:
                self.statistic_url = 'https://vk.com/stats?gid={group_id_int}'.format(group_id_int=self.group_id)

        super(Group, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.domain_or_id, self.name)

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'


class AdRecord(models.Model):
    ad_record_id = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='ad_records')
    post_in_group_date = models.DateTimeField()
