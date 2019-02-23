# Generated by Django 2.0.5 on 2019-01-22 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0042_backgroundabstraction'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_background_abstraction_enabled',
            field=models.BooleanField(default=False, verbose_name='Переносить картинку в шаблон CD-диска?'),
        ),
        migrations.AddField(
            model_name='group',
            name='last_used_background_abstraction_id',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
