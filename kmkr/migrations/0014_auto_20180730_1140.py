# Generated by Django 2.0.3 on 2018-07-30 18:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kmkr', '0013_auto_20180729_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualPlayListEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.IntegerField(help_text='The position of the track in the playlist.')),
                ('artist', models.CharField(blank=True, help_text='The artist who performed the track.', max_length=128)),
                ('title', models.CharField(blank=True, help_text='The title of the track.', max_length=128)),
                ('duration', models.DurationField(blank=True, help_text='The duration of the track.')),
            ],
        ),
        migrations.CreateModel(
            name='ShowInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, help_text='The date on which this instance of the show aired.', null=True)),
                ('host_checked_in', models.TimeField(blank=True, help_text='Specify for original live broadcast, but not for repeat broadcasts.', null=True)),
                ('repeat_of', models.ForeignKey(blank=True, help_text='Specify the previous live instance of this show, if this is a repeat broadcast.', null=True, on_delete=django.db.models.deletion.PROTECT, to='kmkr.ShowInstance')),
                ('show', models.ForeignKey(blank=True, help_text='The show info.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='kmkr.Show')),
            ],
        ),
        migrations.RemoveField(
            model_name='manualplaylist',
            name='show',
        ),
        migrations.DeleteModel(
            name='ManualPlayList',
        ),
        migrations.AddField(
            model_name='manualplaylistentry',
            name='live_show_instance',
            field=models.ForeignKey(help_text='The associated show.', on_delete=django.db.models.deletion.CASCADE, to='kmkr.ShowInstance'),
        ),
    ]