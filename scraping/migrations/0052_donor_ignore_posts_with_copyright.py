# Generated by Django 2.0.5 on 2020-10-06 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0051_auto_20200910_1755'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='ignore_posts_with_copyright',
            field=models.BooleanField(default=False, verbose_name='Игнорировать посты с источником'),
        ),
    ]
