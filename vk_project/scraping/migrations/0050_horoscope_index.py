# Generated by Django 2.0.5 on 2020-09-10 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0049_merge_20200904_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='horoscope',
            name='index',
            field=models.IntegerField(default=0),
        ),
    ]
