# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_auto_20150708_1451'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermitRenewal',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('when', models.DateTimeField(help_text='Date/time on which the parking permit was renewed.')),
            ],
            options={
                'ordering': ['when'],
            },
        ),
        migrations.AddField(
            model_name='parkingpermit',
            name='is_in_inventoried_space',
            field=models.BooleanField(help_text='True if the item is in our inventoried space/building(s). False if the owner has taken it home.', default=True),
        ),
        migrations.AddField(
            model_name='permitrenewal',
            name='permit',
            field=models.ForeignKey(to='inventory.ParkingPermit', help_text='The parking permit that was renewed.', related_name='renewals'),
        ),
    ]
