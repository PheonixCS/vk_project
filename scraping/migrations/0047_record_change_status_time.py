# Generated by Django 2.0.5 on 2020-08-02 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0046_horoscope_copyright_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='change_status_time',
            field=models.DateTimeField(null=True),
        ),
    ]
