# Generated by Django 3.2.23 on 2024-10-09 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0019_alter_filter_answers'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeywordMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.TextField()),
                ('keyword', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]