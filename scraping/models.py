from random import randint

from django.db import models
from django.db.models import Count
from django.utils import timezone


class Donor(models.Model):
    id = models.CharField(max_length=32, verbose_name='Domain/id группы донора', primary_key=True)
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    name = models.CharField(max_length=128, verbose_name='Название', blank=True, default='')
    is_involved = models.BooleanField(default=True, verbose_name='Донор задействован?')
    is_banned = models.BooleanField(default=False, verbose_name='Донор забанен')
    average_views_number = models.IntegerField(
        null=True, verbose_name='Среднее количество просмотров поста', blank=True)

    # Standard
    def save(self, *args, **kwargs):
        self.url = 'https://vk.com/club{}'.format(self.id)
        return super(Donor, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.id, self.name)

    class Meta:
        verbose_name = 'Источник'
        verbose_name_plural = 'Источники'

    # Custom
    def ban(self):
        self.is_banned = True
        self.save(update_fields=['is_banned'])


class Filter(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='filters')
    min_text_length = models.IntegerField(blank=True, null=True,
                                          verbose_name='Минимальная длина текста')
    min_quantity_of_line_breaks = models.IntegerField(blank=True, null=True,
                                                      verbose_name='Минимальное количество переносов строк')
    min_quantity_of_videos = models.IntegerField(blank=True, null=True,
                                                 verbose_name='Минимальное количество видео')
    min_quantity_of_films = models.IntegerField(blank=True, null=True,
                                                verbose_name='Минимальное количество фильмов '
                                                             '(видео длинной от 20 минут)')
    min_quantity_of_images = models.IntegerField(blank=True, null=True,
                                                 verbose_name='Минимальное количество изображений')
    min_quantity_of_gifs = models.IntegerField(blank=True, null=True,
                                               verbose_name='Минимальное количество гифок')
    min_quantity_of_audios = models.IntegerField(blank=True, null=True,
                                                 verbose_name='Минимальное количество аудиозаписей')

    def __str__(self):
        return 'Фильтр #{} для группы {}'.format(self.id, self.donor)


class Record(models.Model):
    NEW = 1
    READY = 2
    POSTING = 3
    POSTED = 4
    FAILED = 5

    STATUS_CHOICES = (
        (NEW, 'new'),
        (READY, 'ready'),
        (POSTING, 'posting'),
        (POSTED, 'posted'),
        (FAILED, 'failed'),
    )

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='records', verbose_name='Источник')
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='records', null=True,
                              verbose_name='Сообщество')
    donor_url = models.URLField(max_length=128, blank=True, default='')
    group_url = models.URLField(max_length=128, blank=True, default='')
    record_id = models.IntegerField(null=True)
    likes_count = models.IntegerField(null=True)
    reposts_count = models.IntegerField(null=True)
    views_count = models.IntegerField(null=True)
    text = models.TextField(max_length=2048, null=True)
    rate = models.IntegerField(null=True)
    post_in_donor_date = models.DateTimeField(null=True)
    add_to_db_date = models.DateTimeField(null=True, auto_now_add=True)
    post_in_group_date = models.DateTimeField(null=True, verbose_name='Дата постинга в сообществе')
    post_in_group_id = models.IntegerField(null=True)
    failed_date = models.DateTimeField(null=True)
    females_count = models.IntegerField(default=0, verbose_name='Лайков от женщин')
    males_count = models.IntegerField(default=0, verbose_name='Лайков от мужчин')
    males_females_ratio = models.FloatField(default=1.0, verbose_name='Соотношение мужчин к женщинам в лайках')
    unknown_count = models.IntegerField(default=0, verbose_name='Лайков от неопределенного пола')
    status = models.IntegerField(choices=STATUS_CHOICES, default=NEW, verbose_name='Статус записи')

    def save(self, *args, **kwargs):
        if self.record_id:
            self.donor_url = f'https://vk.com/wall-{self.donor_id}_{self.record_id}'
        if self.post_in_group_id:
            self.group_url = f'https://vk.com/wall-{self.group_id}_{self.post_in_group_id}'

        super(Record, self).save(*args, **kwargs)

    def get_attachments_count(self):
        gif_count = self.gifs.count()
        image_count = self.images.count()
        video_count = self.videos.count()
        audio_count = self.audios.count()

        return sum([gif_count, image_count, video_count, audio_count])

    def fail(self):
        self.status = self.FAILED
        self.failed_date = timezone.now()
        self.save(update_fields=['status', 'failed_date'])

    def __str__(self):
        return '{}'.format(self.record_id)

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Image(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='images')
    url = models.CharField(max_length=256)


class Gif(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='gifs')
    url = models.CharField(max_length=256)
    owner_id = models.IntegerField(null=True)
    gif_id = models.IntegerField(null=True)


class Audio(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='audios')
    owner_id = models.IntegerField(null=True)
    audio_id = models.IntegerField(null=True)
    artist = models.CharField(max_length=128, null=True)
    genre = models.CharField(max_length=128, null=True)


class Video(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='videos')
    owner_id = models.IntegerField(null=True)
    video_id = models.IntegerField(null=True)


class Horoscope(models.Model):
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='horoscopes')
    zodiac_sign = models.CharField(max_length=128, null=True)
    text = models.TextField(max_length=2048, null=True)
    post_in_group_date = models.DateTimeField(null=True)
    add_to_db_date = models.DateTimeField(null=True, auto_now_add=True)


class Movie(models.Model):
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='movies', null=True)
    title = models.CharField(max_length=256)
    rating = models.FloatField(null=True)
    release_year = models.IntegerField(null=True)
    runtime = models.CharField(null=True, max_length=16)
    overview = models.CharField(max_length=2048, null=True)
    poster = models.CharField(max_length=256, null=True)
    production_country_code = models.CharField(max_length=2, null=True)
    post_in_group_date = models.DateTimeField(null=True, verbose_name='Дата постинга в сообществе')


class Genre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='genres')
    name = models.CharField(max_length=64)


class TrailerManager(models.Manager):
    def random(self):
        count = self.aggregate(ids=Count('id'))['ids']
        random_index = randint(0, count - 1)
        return self.all()[random_index]


class Trailer(models.Model):
    NEW_STATUS = 1
    PENDING_STATUS = 2
    DOWNLOADED_STATUS = 3
    UPLOADED_STATUS = 4
    POSTED_STATUS = 5
    FAILED_STATUS = 6

    STATUS_CHOICES = (
        (NEW_STATUS, 'new'),
        (PENDING_STATUS, 'pending'),
        (DOWNLOADED_STATUS, 'downloaded'),
        (UPLOADED_STATUS, 'uploaded'),
        (POSTED_STATUS, 'posted'),
        (FAILED_STATUS, 'failed')
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=NEW_STATUS, verbose_name='Статус')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='trailers')
    url = models.CharField(max_length=128)
    vk_url = models.CharField(max_length=256, null=True)
    # TODO it should be django's file field, but i'm hurry (and lazy)
    file_path = models.CharField(max_length=256)

    objects = TrailerManager()


class Frame(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='frames')
    url = models.CharField(max_length=256)


class Attachment(models.Model):
    AUDIO = 'audio'
    VIDEO = 'video'
    GIF = 'gif'
    PICTURE = 'picture'

    TYPE_CHOICES = (
        (AUDIO, 'audio'),
        (VIDEO, 'video'),
        (GIF, 'gif'),
        (PICTURE, 'picture')
    )
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='attachments', null=True)
    h_record = models.ForeignKey(Horoscope, on_delete=models.CASCADE, related_name='attachments', null=True)

    data_type = models.CharField(choices=TYPE_CHOICES, max_length=16)
    origin_url = models.URLField(null=True)
    vk_attachment_id = models.CharField(null=True, max_length=200)


class ScrapingHistory(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    group = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='history')

    filter_name = models.CharField(max_length=100, default='unknown')
    filtered_number = models.IntegerField()

    class Meta:
        verbose_name = 'История скрапинга'
        verbose_name_plural = 'История скрапинга'

