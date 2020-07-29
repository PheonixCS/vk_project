import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from posting.models.user import User
from scraping.models import Attachment


class Group(models.Model):
    COMMON = 'common'
    MOVIE_COMMON = 'movie common'
    MOVIE_SPECIAL = 'movie special'
    MUSIC_COMMON = 'music common'
    HOROSCOPES_COMMON = 'horoscopes common'
    HOROSCOPES_MAIN = 'horoscopes main'

    GROUP_TYPE_CHOICES = (
        (COMMON, 'Обычная'),
        (MOVIE_COMMON, 'Обычные фильмы'),
        (MOVIE_SPECIAL, 'Сторонние фильмы'),
        (MUSIC_COMMON, 'Обычная музыка'),
        (HOROSCOPES_COMMON, 'Обычные гороскопы'),
        (HOROSCOPES_MAIN, 'Основные гороскопы')
    )

    domain_or_id = models.CharField(max_length=32, verbose_name='Domain/id группы цели', primary_key=True)
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    group_type = models.CharField(choices=GROUP_TYPE_CHOICES, max_length=128, verbose_name='Тип группы', default=COMMON)
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
    banned_origin_attachment_types = ArrayField(
        models.CharField(choices=Attachment.TYPE_CHOICES, blank=True, null=True, max_length=16),
        blank=True,
        null=True,
        verbose_name='Недопустимые вложения для записей',
        help_text=f'Типы вложений записей, которые не нужны в этой группе. '
        f'Примеры:{[c[1] for c in Attachment.TYPE_CHOICES]}'
    )

    posting_interval = models.IntegerField(
        default=60,
        validators=[MaxValueValidator(1410), MinValueValidator(30)],
        verbose_name='Интервал постинга',
        help_text='Количество минут между постингом. Минимально - 30 минут. Максимально - 1410 (сутки).'
    )
    posting_minute_base = models.IntegerField(
        default=0,
        validators=[MaxValueValidator(59), MinValueValidator(0)],
        verbose_name='Минута отчета',
        help_text='С этой минуты будет начинаться отчёт постинга.'
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

    def get_auditory_percents(self):
        sum_of_auditory = (self.male_weekly_average_count + self.female_weekly_average_count)

        if sum_of_auditory == 0:
            return 0.5, 0.5

        male_percent = self.male_weekly_average_count / sum_of_auditory
        female_percent = 1 - male_percent

        return male_percent, female_percent

    def return_posting_time_list(self):
        result = []

        minutes = self.posting_minute_base

        while minutes < 1440:
            hour = minutes // 60
            posting_minute = minutes % 60
            result.append((hour, posting_minute))
            minutes += self.posting_interval

        return result

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'
