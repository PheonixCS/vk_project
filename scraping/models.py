from django.db import models


class Donor(models.Model):
    id = models.CharField(max_length=32, verbose_name='Domain/id группы донора', primary_key=True)


class Filter(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.DO_NOTHING)
    min_quantity_of_line_breaks = models.IntegerField(blank=True, null=True)
    min_quantity_of_videos = models.IntegerField(blank=True, null=True)
    min_quantity_of_images = models.IntegerField(blank=True, null=True)
    min_quantity_of_gifs = models.IntegerField(blank=True, null=True)
    min_text_length = models.IntegerField(blank=True, null=True)


class Record(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.DO_NOTHING)
    text = models.TextField(max_length=2048, null=True)
    rate = models.IntegerField(null=True)
    post_in_donor_date = models.DateTimeField(null=True)
    add_to_db_date = models.DateTimeField(null=True)
    post_in_group_date = models.DateTimeField(null=True)


class Image(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    url = models.CharField(max_length=128)


class Video(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    owner_id = models.IntegerField()
    video_id = models.IntegerField()

    def get_url(self):
        return 'https://vk.com/video{}_{}'.format(self.owner_id, self.id)