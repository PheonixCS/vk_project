# Generated by Django 3.2.23 on 2024-03-17 14:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0054_auto_20211209_0417'),
        ('tg_core', '0006_delete_bot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='internal_horoscope_sources',
            field=models.ManyToManyField(blank=True, null=True, to='tg_core.InternalHoroscopeSource'),
        ),
        migrations.AlterField(
            model_name='internalhoroscopesourcelink',
            name='link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg_core.internalhoroscopesource'),
        ),
        migrations.AlterField(
            model_name='internalhoroscopesourcelink',
            name='source_post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='scraping.horoscope'),
        ),
        migrations.AlterField(
            model_name='internalhoroscopesourcelink',
            name='target_post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tg_core.tgpost'),
        ),
        migrations.AlterField(
            model_name='tgpost',
            name='tg_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]