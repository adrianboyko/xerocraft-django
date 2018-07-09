# Generated by Django 2.0.3 on 2018-07-01 23:01

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('kmkr', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(default=django.utils.timezone.now, help_text='The date & time that airing of item began.')),
                ('duration', models.DurationField(help_text='The expected duration of the item.')),
                ('title', models.CharField(help_text='The title of the item.', max_length=128)),
                ('artist', models.CharField(help_text='The artist/dj/etc featured in this item.', max_length=128)),
                ('track_id', models.IntegerField(help_text='The track ID of the item in the Radio DJ database.')),
                ('track_type', models.IntegerField(help_text='The type of the item in the Radio DJ database.')),
            ],
        ),
    ]