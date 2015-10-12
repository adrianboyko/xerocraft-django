# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20150830_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitevent',
            name='event_type',
            field=models.CharField(choices=[('A', 'Arrival'), ('P', 'Presence'), ('D', 'Departure')], max_length=1, help_text='The type of visit event.'),
        ),
    ]
