# Generated by Django 2.0.5 on 2018-09-07 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0033_auto_20180906_1706'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='preferred_audience',
        ),
        migrations.AddField(
            model_name='group',
            name='female_weekly_average_count',
            field=models.IntegerField(default=0, verbose_name='Среднее количество мужчин за неделю'),
        ),
        migrations.AddField(
            model_name='group',
            name='male_weekly_average_count',
            field=models.IntegerField(default=0, verbose_name='Среднее количество мужчин за неделю'),
        ),
    ]