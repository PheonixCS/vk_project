# Generated by Django 2.0.5 on 2019-01-03 08:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0031_auto_20181228_0952'),
    ]

    operations = [
        migrations.RenameField(
            model_name='audio',
            old_name='title',
            new_name='genre',
        ),
    ]