# Generated by Django 2.0.5 on 2018-06-18 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0014_auto_20180612_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='failed_date',
            field=models.DateTimeField(null=True),
        ),
    ]
