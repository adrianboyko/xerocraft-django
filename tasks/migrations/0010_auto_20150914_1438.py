# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_auto_20150914_1421'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='task',
            name='end_time',
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='start_time',
            field=models.TimeField(null=True, help_text='The time at which the task should begin, if any.', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='start_time',
            field=models.TimeField(null=True, help_text='The time at which the task should begin, if any.', blank=True),
        ),
    ]
