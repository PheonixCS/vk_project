# Generated by Django 2.0.5 on 2019-01-19 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0030_movie_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='trailer',
            name='vk_url',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
