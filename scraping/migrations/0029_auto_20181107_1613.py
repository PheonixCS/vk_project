# Generated by Django 2.0.5 on 2018-11-07 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0028_auto_20181020_0751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trailer',
            name='file_path',
            field=models.CharField(max_length=256),
        ),
    ]
