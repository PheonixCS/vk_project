# Generated by Django 3.2.23 on 2024-09-22 21:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0017_alter_filter_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filter',
            options={'permissions': [('moderation.view_filter', 'Can view filter'), ('moderation.change_filter', 'Can change filter'), ('moderation.add_filter', 'Can add filter'), ('moderation.delete_filter', 'Can delete filter')]},
        ),
    ]
