# Generated by Django 2.0.5 on 2021-04-06 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0052_donor_ignore_posts_with_copyright'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='max_text_length',
            field=models.IntegerField(blank=True, null=True, verbose_name='Максимальная длина текста'),
        ),
    ]