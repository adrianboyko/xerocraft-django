# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_auto_20150909_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='duration',
            field=models.DurationField(blank=True, help_text='The duration of the task, if applicable. This is elapsed time, not work time.', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='duration',
            field=models.DurationField(blank=True, help_text='The duration of the task, if applicable. This is elapsed time, not work time.', null=True),
        ),
    ]
