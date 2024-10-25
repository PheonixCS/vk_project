# Generated by Django 2.0.5 on 2018-05-12 08:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0002_group_posting_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='donors',
            field=models.ManyToManyField(blank=True, null=True, to='scraping.Donor'),
        ),
        migrations.AlterField(
            model_name='group',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='posting.User'),
        ),
        migrations.AlterField(
            model_name='user',
            name='app_service_token',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Сервисный ключ приложения'),
        ),
    ]