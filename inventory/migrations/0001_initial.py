# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0025_auto_20150702_1643'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('short_desc', models.CharField(help_text='A short description/name for the location.', max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='ParkingPermit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(help_text='Date/time on which the parking permit was created.')),
                ('short_desc', models.CharField(help_text='A short description of the item parked.', max_length=40)),
                ('owner', models.ForeignKey(help_text='The member who owns the parked item.', to='tasks.Member', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='PermitScan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('when', models.DateTimeField(help_text='Date/time on which the parking permit was created.')),
                ('permit', models.ForeignKey(help_text='The parking permit that was scanned', to='inventory.ParkingPermit')),
                ('where', models.ForeignKey(help_text='The location at which the parking permit was scanned.', to='inventory.Location', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
    ]
