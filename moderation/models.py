from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models


class ModerationRule(models.Model):
    id_white_list = models.TextField(max_length=1024,
                                     verbose_name='White list domain/id людей или сообществ (через пробел)',
                                     blank=True, null=True)
    words_stop_list = models.TextField(max_length=1024, verbose_name='Ключевые слова для удаления (через пробел)',
                                       blank=True, null=True)

    def save(self, *args, **kwargs):
        if ModerationRule.objects.exists() and not self.pk:
            raise ValidationError('There is can be only one ModerationRule instance')
        return super(ModerationRule, self).save(*args, **kwargs)

    def __str__(self):
        return 'Правило модерации'

    class Meta:
        app_label = 'posting'
        verbose_name = 'Правило модерации'
        verbose_name_plural = 'Правила модерации'


class WebhookTransaction(models.Model):
    UNPROCESSED = 1
    PROCESSED = 2
    ERROR = 3

    STATUSES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    date_received = models.DateTimeField(auto_now_add=True)
    body = JSONField(default=dict)
    status = models.CharField(max_length=250, choices=STATUSES, default=UNPROCESSED)

    def __str__(self):
        return '{}'.format(self.date_received)


class Comment(models.Model):
    date_processed = models.DateTimeField(auto_now_add=True)
    webhook_transaction = models.OneToOneField(WebhookTransaction, on_delete=models.CASCADE)

    post_id = models.IntegerField(null=True, verbose_name='идентификатор записи')
    post_owner_id = models.IntegerField(null=True, verbose_name='идентификатор владельца записи')
    comment_id = models.IntegerField(null=True, verbose_name='идентификатор комментария')
    from_id = models.IntegerField(null=True, verbose_name='идентификатор автора комментария')
    date = models.IntegerField(null=True, verbose_name='дата создания комментария в формате Unixtime')
    text = models.CharField(max_length=4096, default=None, verbose_name='текст комментария')
    reply_to_user = models.IntegerField(null=True, verbose_name='идентификатор пользователя или сообщества, '
                                                                'в ответ которому оставлен текущий комментарий')
    reply_to_comment = models.IntegerField(null=True, verbose_name='идентификатор комментария, '
                                                                   'в ответ на который оставлен текущий')

    def __str__(self):
        return '{}'.format(self.comment_id)


class Attachment(models.Model):
    attached_to = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='attachments')
    type = models.CharField(max_length=64, default='')
    body = JSONField(default=dict)
