# Generated by Django 2.0.5 on 2019-05-14 22:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0040_auto_20190505_1751'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapingHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('filter_name', models.CharField(default='unknown', max_length=100)),
                ('filtered_number', models.IntegerField()),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='scraping.Donor')),
            ],
            options={
                'verbose_name': 'История скрапинга',
                'verbose_name_plural': 'История скрапинга',
            },
        ),
    ]