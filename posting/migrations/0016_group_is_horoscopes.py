# Generated by Django 2.0.5 on 2018-06-25 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0015_merge_20180613_0232'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_horoscopes',
            field=models.BooleanField(default=False, verbose_name='Постинг гороскопов задействован?'),
        ),
    ]