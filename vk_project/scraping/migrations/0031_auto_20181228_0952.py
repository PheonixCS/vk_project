# Generated by Django 2.0.5 on 2018-12-28 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0030_movie_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='audio',
            name='artist',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='audio',
            name='title',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
