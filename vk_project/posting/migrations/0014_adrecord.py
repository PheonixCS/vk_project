# Generated by Django 2.0.5 on 2018-06-13 01:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0013_group_is_pin_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ad_record_id', models.IntegerField()),
                ('post_in_group_date', models.DateTimeField()),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ad_records', to='posting.Group')),
            ],
        ),
    ]
