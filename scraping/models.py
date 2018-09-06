from django.db import models


class Donor(models.Model):
    id = models.CharField(max_length=32, verbose_name='Domain/id группы донора', primary_key=True)
    url = models.URLField(max_length=128, verbose_name='Ссылка', blank=True, default='')
    name = models.CharField(max_length=128, verbose_name='Название', blank=True, default='')
    is_involved = models.BooleanField(default=True, verbose_name='Донор задействован?')

    def save(self, *args, **kwargs):
        self.url = 'https://vk.com/club{}'.format(self.id)
        return super(Donor, self).save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.id, self.name)

    class Meta:
        verbose_name = 'Источник'
        verbose_name_plural = 'Источники'


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
    is_involved_now = models.BooleanField(default=False)
    females_count = models.IntegerField(default=0, verbose_name='Лайков от женщин')
    males_count = models.IntegerField(default=0, verbose_name='Лайков от мужчин')
    males_females_ratio = models.FloatField(default=1.0, verbose_name='Соотношение мужчин к женщинам в лайках')
    unknown_count = models.IntegerField(default=0, verbose_name='Лайков от неопределенного пола')

    def save(self, *args, **kwargs):
        if self.record_id:
            self.donor_url = f'https://vk.com/wall-{self.donor_id}_{self.record_id}'
        if self.post_in_group_id:
            self.group_url = f'https://vk.com/wall-{self.group_id}_{self.post_in_group_id}'

        super(Record, self).save(*args, **kwargs)

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


class Video(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='videos')
    owner_id = models.IntegerField(null=True)
    video_id = models.IntegerField(null=True)


class Horoscope(models.Model):
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='horoscopes')
    zodiac_sign = models.CharField(max_length=128, null=True)
    text = models.TextField(max_length=2048, null=True)
    post_in_group_date = models.DateTimeField(null=True)
    image_url = models.CharField(max_length=256, null=True)
    post_in_donor_date = models.DateTimeField(null=True)
    add_to_db_date = models.DateTimeField(null=True, auto_now_add=True)
