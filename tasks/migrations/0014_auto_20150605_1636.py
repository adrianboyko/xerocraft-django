# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_auto_20150605_1529'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='repeat_delay',
            new_name='repeat_interval',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='on_demand',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='flexible_dates',
            field=models.NullBooleanField(default=None, help_text="Select 'No' if this task must occur on specific regularly-spaced dates.<br/>Select 'Yes' if the task is like an oil change that should happen every 90 days, but not on any specific date.", choices=[(True, 'Yes'), (False, 'No'), (None, 'N/A')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_accepted',
            field=models.NullBooleanField(verbose_name=[(True, 'Yes'), (False, 'No'), (None, 'N/A')]),
        ),
    ]
