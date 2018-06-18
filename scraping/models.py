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
    min_quantity_of_images = models.IntegerField(blank=True, null=True,
                                                 verbose_name='Минимальное количество изображений')
    min_quantity_of_gifs = models.IntegerField(blank=True, null=True,
                                               verbose_name='Минимальное количество гифок')
    min_quantity_of_audios = models.IntegerField(blank=True, null=True,
                                                 verbose_name='Минимальное количество аудиозаписей')

    def __str__(self):
        return 'Фильтр #{} для группы {}'.format(self.id, self.donor)


class Record(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='records')
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, related_name='records', null=True)
    record_id = models.IntegerField(null=True)
    likes_count = models.IntegerField(null=True)
    reposts_count = models.IntegerField(null=True)
    views_count = models.IntegerField(null=True)
    text = models.TextField(max_length=2048, null=True)
    rate = models.IntegerField(null=True)
    post_in_donor_date = models.DateTimeField(null=True)
    add_to_db_date = models.DateTimeField(null=True, auto_now_add=True)
    post_in_group_date = models.DateTimeField(null=True)
    failed_date = models.DateTimeField(null=True)

    def __str__(self):
        return 'record {}'.format(self.record_id)


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
