# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0019_auto_20151012_1320'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='elapsed_duration',
            field=models.DurationField(null=True, help_text='The elapsed time the member plans to work.', blank=True),
        ),
        migrations.AddField(
            model_name='claim',
            name='elapsed_start_time',
            field=models.TimeField(null=True, help_text='The clock time at which the member plans to start work.', blank=True),
        ),
        migrations.AlterField(
            model_name='claim',
            name='hours_claimed',
            field=models.DecimalField(null=True, decimal_places=2, help_text='The actual effort claimed in hours (e.g. 1.25). This is work time, not elapsed time.', blank=True, max_digits=5),
        ),
    ]
