# Generated by Django 2.0.5 on 2019-08-31 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0048_postinghistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_copyright_needed',
            field=models.BooleanField(default=False, verbose_name='Указывать источик в записях'),
        ),
    ]