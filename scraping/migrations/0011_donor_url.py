# Generated by Django 2.0.5 on 2018-05-25 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0010_merge_20180524_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='url',
            field=models.URLField(blank=True, default='', max_length=128, verbose_name='Ссылка'),
        ),
    ]
