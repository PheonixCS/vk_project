from django.db import models

from scraping.models import Record


class MusicGenreEpithet(models.Model):
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='music_genre_epithets')
    text_for_male = models.TextField(max_length=256, default='',
                                     verbose_name='Эпитет для музыкального жанра мужского рода')
    text_for_female = models.TextField(max_length=256, default='',
                                       verbose_name='Эпитет для музыкального жанра женского рода')

    class Meta:
        verbose_name = 'Эпитет'
        verbose_name_plural = 'Эпитеты'


class AdditionalText(models.Model):
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='additional_texts')
    text = models.TextField(max_length=1024, default='',
                            verbose_name='Дополнительный текст, единственное число')
    text_plural = models.TextField(max_length=1024, default='',
                                   verbose_name='Дополнительный текст, множественное число')

    class Meta:
        verbose_name = 'Текст'
        verbose_name_plural = 'Тексты'


class AdRecord(models.Model):
    ad_record_id = models.IntegerField()
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='ad_records')
    post_in_group_date = models.DateTimeField()


class BackgroundAbstraction(models.Model):
    picture = models.ImageField(upload_to='backgrounds')

    def __str__(self):
        return f'{self.id}'

    class Meta:
        app_label = 'posting'


class PostingHistory(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='history')
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='history')

    candidates_number = models.IntegerField()
    candidates_internal_ids = models.CharField(max_length=2500)

    class Meta:
        verbose_name = 'История постинга'
        verbose_name_plural = 'История постинга'


class ServiceToken(models.Model):
    app_service_token = models.CharField(max_length=256, verbose_name='Сервисный ключ приложения', primary_key=True)
    last_used = models.DateTimeField(null=True)

    def __str__(self):
        return self.app_service_token

    class Meta:
        verbose_name = 'Сервисный токен'
        verbose_name_plural = 'Сервисные токены'
