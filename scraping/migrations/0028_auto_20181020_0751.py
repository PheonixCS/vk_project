# Generated by Django 2.0.5 on 2018-10-20 07:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0027_auto_20181016_1714'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productioncountry',
            name='movie',
        ),
        migrations.AddField(
            model_name='movie',
            name='production_country_code',
            field=models.CharField(max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='poster',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.DeleteModel(
            name='ProductionCountry',
        ),
    ]
