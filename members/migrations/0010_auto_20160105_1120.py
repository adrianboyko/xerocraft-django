# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0009_auto_20160105_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitevent',
            name='when',
            field=models.DateTimeField(help_text='Date/time of visit event.', default=django.utils.timezone.now),
        ),
    ]
