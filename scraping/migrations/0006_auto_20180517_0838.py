# Generated by Django 2.0.5 on 2018-05-17 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0005_auto_20180514_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='donor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='scraping.Donor'),
        ),
        migrations.AlterField(
            model_name='record',
            name='donor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='scraping.Donor'),
        ),
        migrations.AlterField(
            model_name='record',
            name='post_in_donor_date',
            field=models.DateTimeField(null=True),
        ),
    ]