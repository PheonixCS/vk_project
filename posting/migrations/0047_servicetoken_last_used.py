# Generated by Django 2.0.5 on 2019-03-31 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0046_remove_group_is_delete_audio_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicetoken',
            name='last_used',
            field=models.DateTimeField(null=True),
        ),
    ]