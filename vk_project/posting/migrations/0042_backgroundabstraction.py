# Generated by Django 2.0.5 on 2019-01-04 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0041_group_is_movies'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackgroundAbstraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picture', models.ImageField(upload_to='backgrounds')),
            ],
        ),
    ]