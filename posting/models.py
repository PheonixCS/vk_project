import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models

from scraping.models import Attachment, Record


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
    last_used = models.DateTimeField(null=True)

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
    is_movies = models.BooleanField(default=False, verbose_name='Постинг из источника фильмов задействован?')
    is_pin_enabled = models.BooleanField(default=True, verbose_name='Закреплять лучшие посты?')
    posting_time = models.TimeField(verbose_name='Время постинга', default=datetime.time(00, 00))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='groups', blank=True, null=True)
    callback_api_token = models.CharField(max_length=128, verbose_name='Ответ для callback api', blank=True, default='')
    donors = models.ManyToManyField('scraping.Donor', blank=True)

    is_text_delete_enabled = models.BooleanField(default=False, verbose_name='Убирать текст из постов?')
    is_text_filling_enabled = models.BooleanField(default=False, verbose_name='Переносить текст на изображение?')
    is_image_mirror_enabled = models.BooleanField(default=False, verbose_name='Отзеркаливать изображения без текста?')
    is_changing_image_to_square_enabled = models.BooleanField(default=False,
                                                              verbose_name='Приводить изображения к '
                                                                           'более квадратному виду?')
    RGB_image_tone = models.CharField(max_length=15, blank=True, default='',
                                      verbose_name='Применять RBG тон к изображениям (R G B factor)')
    is_photos_shuffle_enabled = models.BooleanField(default=False, verbose_name='Перемешивать фото?')
    is_audios_shuffle_enabled = models.BooleanField(default=False, verbose_name='Перемешивать аудиозаписи?')
    is_merge_images_enabled = models.BooleanField(default=False, verbose_name='Объединять 6 изображений в одно?')
    is_replace_russian_with_english = models.BooleanField(default=False,
                                                          verbose_name='Заменять русские буквы английскими?')
    is_copyright_needed = models.BooleanField(default=False, verbose_name='Указывать источик в записях')

    is_additional_text_enabled = models.BooleanField(default=False,
                                                     verbose_name='Добавлять к записи дополнительный текст?')
    last_used_additional_text_id = models.IntegerField(null=True, default=0)

    is_background_abstraction_enabled = models.BooleanField(default=False,
                                                            verbose_name='Переносить картинку в шаблон CD-диска?')
    last_used_background_abstraction_id = models.IntegerField(null=True, default=0)
    is_music_genre_epithet_enabled = models.BooleanField(default=False,
                                                         verbose_name='Добавлять эпитет перед музыкальным жанром?')
    last_used_music_genre_epithet_id = models.IntegerField(null=True, default=0)

    members_count = models.IntegerField(null=True, verbose_name='Участники')
    members_growth = models.IntegerField(null=True, verbose_name='Прирост')
    number_of_posts_yesterday = models.IntegerField(null=True, verbose_name='Посты за вчера')
    number_of_ad_posts_yesterday = models.IntegerField(null=True, verbose_name='Реклама за вчера')
    statistics_last_update_date = models.DateTimeField(null=True)

    male_weekly_average_count = models.IntegerField(default=0,
                                                    verbose_name='Среднее количество мужчин за неделю')
    female_weekly_average_count = models.IntegerField(default=0,
                                                      verbose_name='Среднее количество женщин за неделю')
    sex_last_update_date = models.DateTimeField(null=True)
    # banned_origin_attachment_types = models.IntegerField(
    #     choices=Attachment.TYPE_CHOICES, blank=True, null=True)
    banned_origin_attachment_types = ArrayField(
        models.CharField(choices=Attachment.TYPE_CHOICES, blank=True, null=True, max_length=16),
        blank=True,
        null=True,
        verbose_name='Недопустимые вложения для записей',
        help_text=f'Типы вложений записей, которые не нужны в этой группе. '
                  f'Примеры:{[c[1] for c in Attachment.TYPE_CHOICES]}'
    )

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


class MusicGenreEpithet(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='music_genre_epithets')
    text_for_male = models.TextField(max_length=256, default='',
                                     verbose_name='Эпитет для музыкального жанра мужского рода')
    text_for_female = models.TextField(max_length=256, default='',
                                       verbose_name='Эпитет для музыкального жанра женского рода')

    class Meta:
        verbose_name = 'Эпитет'
        verbose_name_plural = 'Эпитеты'


class AdditionalText(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='additional_texts')
    text = models.TextField(max_length=1024, default='',
                            verbose_name='Дополнительный текст, единственное число')
    text_plural = models.TextField(max_length=1024, default='',
                                   verbose_name='Дополнительный текст, множественное число')

    class Meta:
        verbose_name = 'Текст'
        verbose_name_plural = 'Тексты'


class AdRecord(models.Model):
    ad_record_id = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='ad_records')
    post_in_group_date = models.DateTimeField()


class BackgroundAbstraction(models.Model):
    picture = models.ImageField(upload_to='backgrounds')

    def __str__(self):
        return f'{self.id}'

    class Meta:
        app_label = 'posting'


class PostingHistory(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='history')
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='history')

    candidates_number = models.IntegerField()
    candidates_internal_ids = models.CharField(max_length=2500)

    class Meta:
        verbose_name = 'История постинга'
        verbose_name_plural = 'История постинга'
