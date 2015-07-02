# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0024_auto_20150702_1553'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parkingpermit',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='permitscan',
            name='permit',
        ),
        migrations.RemoveField(
            model_name='permitscan',
            name='where',
        ),
        migrations.DeleteModel(
            name='Location',
        ),
        migrations.DeleteModel(
            name='ParkingPermit',
        ),
        migrations.DeleteModel(
            name='PermitScan',
        ),
    ]
