# Generated by Django 3.2.23 on 2024-02-03 22:38

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0062_auto_20220214_1828'),
        ('tg_core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='tg_id',
            field=models.IntegerField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='internalhoroscopesource',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='posting.group'),
        ),
        migrations.AddField(
            model_name='internalhoroscopesource',
            name='repost_time',
            field=models.TimeField(default=datetime.time(0, 0), verbose_name='Время постинга из источника'),
        ),
        migrations.AddField(
            model_name='tgpost',
            name='channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg_core.channel'),
        ),
        migrations.AddField(
            model_name='tgpost',
            name='posted_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tgpost',
            name='scheduled_dt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tgpost',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('posting', 'Posting'), ('posted', 'Posted'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('deleted', 'Deleted')], default='draft', max_length=16),
        ),
        migrations.AddField(
            model_name='tgpost',
            name='tg_id',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.CharField(help_text='E.g.: @your_channel_name', max_length=256, unique=True),
        ),
    ]
