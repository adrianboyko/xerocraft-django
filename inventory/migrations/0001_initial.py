# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('x', models.FloatField(blank=True, null=True, help_text='An ordinate in some coordinate system to help locate the location.')),
                ('y', models.FloatField(blank=True, null=True, help_text='An ordinate in some coordinate system to help locate the location.')),
                ('z', models.FloatField(blank=True, null=True, help_text='An ordinate in some coordinate system to help locate the location.')),
                ('short_desc', models.CharField(max_length=40, null=True, help_text='A short description/name for the location.', blank=True)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='ParkingPermit',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('created', models.DateField(auto_now_add=True, help_text='Date/time on which the parking permit was created.')),
                ('short_desc', models.CharField(max_length=40, help_text='A short description of the item parked.')),
                ('ok_to_move', models.BooleanField(help_text='Is it OK to carefully move the item to another location, if necessary?', default=True)),
                ('is_in_inventoried_space', models.BooleanField(help_text='True if the item is in our inventoried space/building(s). False if the owner has taken it home.', default=True)),
                ('owner', models.ForeignKey(to='members.Member', on_delete=django.db.models.deletion.PROTECT, help_text='The member who owns the parked item.')),
            ],
            options={
                'ordering': ['owner', 'created'],
            },
        ),
        migrations.CreateModel(
            name='PermitRenewal',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('when', models.DateTimeField(help_text='Date/time on which the parking permit was renewed.')),
                ('permit', models.ForeignKey(related_name='renewals', to='inventory.ParkingPermit', help_text='The parking permit that was renewed.')),
            ],
            options={
                'ordering': ['when'],
            },
        ),
        migrations.CreateModel(
            name='PermitScan',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('when', models.DateTimeField(help_text='Date/time on which the parking permit was created.')),
                ('permit', models.ForeignKey(related_name='scans', to='inventory.ParkingPermit', help_text='The parking permit that was scanned')),
                ('where', models.ForeignKey(to='inventory.Location', on_delete=django.db.models.deletion.PROTECT, help_text='The location at which the parking permit was scanned.')),
            ],
            options={
                'ordering': ['where', 'when'],
            },
        ),
    ]
