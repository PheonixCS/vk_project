# Generated by Django 2.0.5 on 2018-10-16 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0024_auto_20181016_0020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='overview',
            field=models.CharField(max_length=2048, null=True),
        ),
    ]
