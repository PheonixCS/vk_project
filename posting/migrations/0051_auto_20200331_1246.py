# Generated by Django 2.0.5 on 2020-03-31 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0050_group_group_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='group_type',
            field=models.CharField(choices=[('common', 'Обычная'), ('movie common', 'Обычные фильмы'), ('movie special', 'Сторонние фильмы'), ('music common', 'Обычная музыка'), ('horoscopes common', 'Обычные гороскопы'), ('horoscopes main', 'Основные гороскопы')], default='common', max_length=128, verbose_name='Тип группы'),
        ),
    ]
