# Generated by Django 2.0.5 on 2018-08-25 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posting', '0027_group_is_text_delete_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(default='', max_length=1024, verbose_name='Дополнительный текст')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_texts', to='posting.Group')),
            ],
        ),
    ]
