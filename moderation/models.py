from django.db import models
from django.core.exceptions import ValidationError


class ModerationRule(models.Model):
    id_white_list = models.TextField(max_length=1024, verbose_name='White list domain/id людей или сообществ')
    words_stop_list = models.TextField(max_length=1024, verbose_name='Ключевые слова для удаления (через пробел)')

    def save(self, *args, **kwargs):
        if ModerationRule.objects.exists() and not self.pk:
            raise ValidationError('There is can be only one ModerationRule instance')
        return super(ModerationRule, self).save(*args, **kwargs)
