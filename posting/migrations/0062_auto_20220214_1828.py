# Generated by Django 2.2 on 2022-02-14 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0061_authcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='authcode',
            name='used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_authed',
            field=models.BooleanField(default=False),
        ),
    ]
