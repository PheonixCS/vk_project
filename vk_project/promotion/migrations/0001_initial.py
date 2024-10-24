# Generated by Django 2.2 on 2022-06-26 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PromotionTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.IntegerField()),
                ('status', models.CharField(choices=[('new', 'new'), ('sent', 'sent'), ('failed', 'failed'), ('done', 'done')], default='new', max_length=32)),
                ('created_dt', models.DateTimeField(auto_now_add=True)),
                ('updated_dt', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
