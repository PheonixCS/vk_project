# Generated by Django 2.0.5 on 2018-05-29 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0012_record_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='gif',
            name='gif_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='gif',
            name='owner_id',
            field=models.IntegerField(null=True),
        ),
    ]
