# Generated by Django 2.2 on 2022-02-12 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0060_user_two_factor'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, default='', max_length=8)),
                ('create_dt', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posting.User')),
            ],
        ),
    ]
