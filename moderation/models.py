from django.db import models


class ModerationRule(models.Model):
    id_white_list = models.TextField(max_length=1024, verbose_name='White list domain/id людей или сообществ')
    words_stop_list = models.TextField(max_length=1024, verbose_name='Ключевые слова для удаления')
