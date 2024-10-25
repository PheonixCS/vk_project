# Generated by Django 2.0.5 on 2018-05-19 17:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0007_auto_20180518_0942'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gif',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=256)),
                ('record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gifs', to='scraping.Record')),
            ],
        ),
    ]