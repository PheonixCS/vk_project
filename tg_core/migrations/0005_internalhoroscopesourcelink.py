# Generated by Django 3.2.23 on 2024-02-04 01:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0054_auto_20211209_0417'),
        ('tg_core', '0004_alter_tgpost_tg_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalHoroscopeSourceLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
                ('link', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg_core.internalhoroscopesource')),
                ('source_post', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='scraping.horoscope')),
                ('target_post', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg_core.tgpost')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
