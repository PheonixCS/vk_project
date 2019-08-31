# Generated by Django 2.0.5 on 2019-08-31 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0042_auto_20190622_1053'),
    ]

    operations = [
        migrations.AddField(
            model_name='donor',
            name='is_copyright_needed',
            field=models.BooleanField(default=False, verbose_name='Указывать как источник в записи?'),
        ),
        migrations.AlterField(
            model_name='donor',
            name='ban_reason',
            field=models.IntegerField(blank=True, choices=[(1, 'Нет новых постов'), (2, 'Забанен в вк')], null=True, verbose_name='Причина отключения донора'),
        ),
    ]
