# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_auto_20150707_2033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permitscan',
            name='permit',
            field=models.ForeignKey(related_name='scans', to='inventory.ParkingPermit', help_text='The parking permit that was scanned'),
        ),
    ]
