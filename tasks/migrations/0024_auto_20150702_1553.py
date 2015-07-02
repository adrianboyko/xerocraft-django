# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0023_auto_20150622_1013'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('short_desc', models.CharField(max_length=40, help_text='A short description/name for the location.')),
            ],
        ),
        migrations.CreateModel(
            name='MemberNote',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('content', models.TextField(max_length=2048, help_text='For staff. Anything you want to say about the member.')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tasks.Member', related_name='member_notes_authored', help_text='The member who wrote this note.')),
                ('task', models.ForeignKey(to='tasks.Member')),
            ],
        ),
        migrations.CreateModel(
            name='ParkingPermit',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(help_text='Date/time on which the parking permit was created.')),
                ('short_desc', models.CharField(max_length=40, help_text='A short description of the item parked.')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tasks.Member', help_text='The member who owns the parked item.')),
            ],
        ),
        migrations.CreateModel(
            name='PermitScan',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('when', models.DateTimeField(help_text='Date/time on which the parking permit was created.')),
                ('permit', models.ForeignKey(to='tasks.ParkingPermit', help_text='The parking permit that was scanned')),
                ('where', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tasks.Location', help_text='The location at which the parking permit was scanned.')),
            ],
        ),
        migrations.AlterField(
            model_name='tasknote',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tasks.Member', related_name='task_notes_authored', help_text='The member who wrote this note.'),
        ),
    ]
