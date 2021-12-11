import datetime

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from posting.models.block import Block
from posting.models.user import User
from scraping.models import Attachment, Record, ScrapingHistory


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
    group_id = models.IntegerField(null=True, blank=False)
    is_posting_active = models.BooleanField(default=True, verbose_name='Постинг активен?')
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
        return '{} {} {}'.format(self.domain_or_id, self.name, self.url)

    def __repr__(self):
        return '{} {} {}'.format(self.domain_or_id, self.name, self.url)

    def get_auditory_percents(self):
        sum_of_auditory = (self.male_weekly_average_count + self.female_weekly_average_count)

        if sum_of_auditory == 0:
            return 0.5, 0.5

        male_percent = self.male_weekly_average_count / sum_of_auditory
        female_percent = 1 - male_percent

        return male_percent, female_percent

    def return_posting_time_list(self, base_minute=None, interval=None):
        minutes = base_minute or self.posting_minute_base
        interval = interval or self.posting_interval
        result = []

        while minutes < 1440:
            hour = minutes // 60
            posting_minute = minutes % 60
            result.append((hour, posting_minute))
            minutes += interval

        return result

    def is_blocked(self):
        for block in self.blocks.all():
            if block.is_block_active():
                result = True
                break
        else:
            result = False

        return result

    def set_block(self, reason, period_in_minutes):
        new_block = Block.objects.create()
        new_block.activate(self, reason=reason, period_in_minutes=period_in_minutes)

        return new_block

    def get_next_posting_time(self) -> datetime.datetime:
        now = timezone.now()
        posting_time_intervals = self.return_posting_time_list()
        result = now

        for item in posting_time_intervals:
            item_time = now.replace(hour=item[0], minute=item[1], second=0, microsecond=0)
            result = item_time
            if item_time >= now:
                break

        return result

    def get_active_donors_number(self):
        return self.donors.filter(is_involved=True).count()

    def get_last_record(self):
        latest_record = common_record = self.records.order_by('-post_in_group_date').first()

        if self.horoscopes.exists():
            horoscope_record = self.horoscopes.filter(post_in_group_date__isnull=False) \
                .order_by('-post_in_group_date').first()

            if (
                    common_record
                    and horoscope_record.post_in_group_date
                    and horoscope_record.post_in_group_date > common_record.post_in_group_date
            ):
                latest_record = horoscope_record

        return latest_record

    def get_last_common_record(self):
        common_record = self.records.order_by('-post_in_group_date').first()
        return common_record

    def get_last_record_time(self):
        last_record = self.get_last_record()
        if last_record is not None and last_record.post_in_group_date is not None:
            delta = last_record.post_in_group_date
        else:
            delta = None
        return delta

    def get_ready_records(self):
        now_time_utc = timezone.now()
        allowed_time_threshold = now_time_utc - datetime.timedelta(hours=8)
        return Record.objects.filter(status=Record.READY, donor__group=self,
                                     post_in_donor_date__gte=allowed_time_threshold)

    def get_all_records_last_day(self):
        now = timezone.now()
        day_ago = now - datetime.timedelta(hours=24)

        return Record.objects.filter(donor__group=self, add_to_db_date__gte=day_ago)

    def filter_stats_last_day(self):
        filters = dict()

        now = timezone.now()
        day_ago = now - datetime.timedelta(hours=24)

        for filter_history in ScrapingHistory.objects.filter(group__group=self, created_at__gte=day_ago):
            filter_data = filters.get(filter_history.filter_name, 0) + filter_history.filtered_number
            filters.update({filter_history.filter_name: filter_data})

        return filters.items()

    def is_post_time_in_interval(self):
        if self.get_last_record_time():
            delta = int((timezone.now() - self.get_last_record_time()).seconds // 60)
        else:
            delta = False
        return delta and delta <= self.posting_interval

    def do_need_post_after_ad(self):
        result = False
        if self.are_any_ads_posted_recently():
            # если у нас есть рекламный пост последний час и 5 минут - нельзя постить
            result = False
        elif self.ad_records.exists():
            # если есть рекламный пост и он последний в ленте - нужно "догнать" обычный пост
            last_hour_ads = self.ad_records.order_by('-post_in_group_date').first()
            last_post = self.get_last_record()

            if last_hour_ads.post_in_group_date > last_post.post_in_group_date:
                result = True

        return result

    def are_any_ads_posted_recently(self) -> bool:
        now_time_utc = timezone.now()
        ads_time_threshold = now_time_utc - datetime.timedelta(hours=1, minutes=5)

        last_hour_ads = self.ad_records.filter(post_in_group_date__gt=ads_time_threshold)
        if last_hour_ads.exists():
            return True

        return False

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'
