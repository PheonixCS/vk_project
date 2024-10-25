from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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


# Модель для хранения коментов которые ждут проверки на подписку
class UserDataSubscribe(models.Model):
    user_id = models.TextField()
    group_id = models.TextField()
    comment_id = models.TextField()
    post_id = models.TextField()
    owner_id = models.TextField() 

    @classmethod
    def add_user(cls, user_id, group_id, comment_id, post_id, owner_id):
        cls.objects.create(user_id=user_id, group_id=group_id, comment_id=comment_id, post_id=post_id, owner_id=owner_id)

    @classmethod
    def clear_model(cls):
        cls.objects.all().delete()

# Модель для добавления ключевиков через админку
class Filter(models.Model):
    keywords = models.TextField(help_text="Введите ключевые слова через ';'")
    answers = models.FileField(upload_to='', default='file.txt', help_text="Загрузите файл .txt с ответами.")
    onlyword = models.BooleanField(default=False, help_text="Искать слова в предложении? (True/False)")

    def __str__(self):
        return self.keywords
    
    class Meta:
        permissions = [
            ("moderation.view_filter", "Can view filter"),
            ("moderation.change_filter", "Can change filter"),
            ("moderation.add_filter", "Can add filter"),
            ("moderation.delete_filter", "Can delete filter"),
        ]
        
# Модель для записи времени последнего комментария отправленого пользователем с определенным ключевым словом        
class KeywordMessage(models.Model):
    user_id = models.TextField()
    keyword = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    @classmethod
    def add_or_update_message(cls, user_id, keyword):
        # Проверяем, есть ли уже сообщение с таким ключевым словом
        last_message = cls.last_message_with_keyword(user_id, keyword)
        if last_message:
            # Если сообщение существует, обновляем его текст и время
            last_message.timestamp = timezone.now()
            last_message.save(update_fields=['timestamp'])
        else:
            # Если нет, создаем новое сообщение
            cls.objects.create(user_id=user_id, keyword=keyword)

    @classmethod
    def last_message_with_keyword(cls, user_id, keyword):
        try:
            return cls.objects.filter(user_id=user_id, keyword=keyword).latest('timestamp')
        except cls.DoesNotExist:
            return None

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

##Модель с токеном
class Token(models.Model):
    is_community_token = models.BooleanField(default=False)
    access_token = models.TextField(max_length=512, verbose_name="Access Token")
    access_token_lifetime = models.TextField(max_length=512, verbose_name="Access Token Lifetime", blank=True, null=True)
    refresh_token = models.TextField(max_length=512, verbose_name="Refresh Token", blank=True, null=True)
    refresh_token_lifetime = models.TextField(max_length=512, verbose_name="Refresh Token Lifetime", blank=True, null=True)
    device_id = models.TextField(max_length=512, verbose_name="Device ID", blank=True, null=True)
    app_id = models.TextField(max_length=512, verbose_name="App ID", blank=True, null=True)
#Сохранение данных с коллбэков авторизации
class AuthorizationTransactions(models.Model):
    state=models.CharField(max_length=256)
    code_verifier=models.CharField(max_length=128)
    app_id=models.CharField(max_length=256)
