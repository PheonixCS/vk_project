# Generated by Django 3.2.23 on 2024-06-10 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0055_horoscope_rates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gif',
            name='url',
            field=models.CharField(max_length=2048),
        ),
        migrations.AlterField(
            model_name='image',
            name='url',
            field=models.CharField(max_length=2048),
        ),
    ]
