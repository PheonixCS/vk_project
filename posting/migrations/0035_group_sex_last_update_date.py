# Generated by Django 2.0.5 on 2018-09-08 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0034_auto_20180907_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='sex_last_update_date',
            field=models.DateTimeField(null=True),
        ),
    ]