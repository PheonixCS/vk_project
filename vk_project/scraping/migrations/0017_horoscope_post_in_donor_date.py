# Generated by Django 2.0.5 on 2018-06-26 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0016_horoscope'),
    ]

    operations = [
        migrations.AddField(
            model_name='horoscope',
            name='post_in_donor_date',
            field=models.DateTimeField(null=True),
        ),
    ]