# Generated by Django 2.0.5 on 2018-10-16 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0026_auto_20181016_0102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='runtime',
            field=models.CharField(max_length=16, null=True),
        ),
    ]