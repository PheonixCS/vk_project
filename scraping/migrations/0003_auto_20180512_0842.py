# Generated by Django 2.0.5 on 2018-05-12 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0002_auto_20180506_2004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='min_quantity_of_gifs',
            field=models.IntegerField(blank=True, null=True, verbose_name='Минимальное количество гифок'),
        ),
        migrations.AlterField(
            model_name='filter',
            name='min_quantity_of_images',
            field=models.IntegerField(blank=True, null=True, verbose_name='Минимальное количество изображений'),
        ),
        migrations.AlterField(
            model_name='filter',
            name='min_quantity_of_line_breaks',
            field=models.IntegerField(blank=True, null=True, verbose_name='Минимальное количество переносов строк'),
        ),
        migrations.AlterField(
            model_name='filter',
            name='min_quantity_of_videos',
            field=models.IntegerField(blank=True, null=True, verbose_name='Минимальное количество видео'),
        ),
        migrations.AlterField(
            model_name='filter',
            name='min_text_length',
            field=models.IntegerField(blank=True, null=True, verbose_name='Минимальная длина текста'),
        ),
    ]