# Generated by Django 3.2.23 on 2024-02-02 20:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
                ('name', models.CharField(max_length=64)),
                ('token', models.CharField(max_length=64)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InternalHoroscopeSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TGPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
                ('text', models.TextField(blank=True, default='', max_length=4096)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TGAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
                ('file', models.FileField(upload_to='tg_attachments/')),
                ('file_type', models.CharField(choices=[('image', 'Image')], default='image', max_length=64)),
                ('telegram_file_id', models.CharField(blank=True, default='', max_length=256)),
                ('post', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tg_core.tgpost')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_dt', models.DateTimeField(editable=False)),
                ('modified_dt', models.DateTimeField(editable=False)),
                ('name', models.CharField(max_length=256, unique=True)),
                ('is_active', models.BooleanField(default=False)),
                ('internal_horoscope_sources', models.ManyToManyField(to='tg_core.InternalHoroscopeSource')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
