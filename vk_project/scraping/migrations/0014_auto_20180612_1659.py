# Generated by Django 2.0.5 on 2018-06-12 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0013_auto_20180529_1617'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='donor',
            options={'verbose_name': 'Источник', 'verbose_name_plural': 'Источники'},
        ),
    ]
