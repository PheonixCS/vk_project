# Generated by Django 2.0.5 on 2018-05-25 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0009_merge_20180524_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='callback_api_token',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='Ответ для callback api'),
        ),
    ]
