# Generated by Django 2.0.5 on 2018-05-24 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0008_gif'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='name',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='Название'),
        ),
    ]
