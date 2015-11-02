# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0024_auto_20151026_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='work_duration',
            field=models.DurationField(blank=True, help_text='Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_duration',
            field=models.DurationField(blank=True, help_text='Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.', null=True),
        ),
    ]
