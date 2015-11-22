# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0026_auto_20151121_2012'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='orig_sched_date',
            field=models.DateField(blank=True, help_text='This is the first value that scheduled_date was set to. Required to avoid recreating a rescheduled task.', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='creation_date',
            field=models.DateField(help_text='The date on which this task was created in the database.', default=datetime.date.today),
        ),
    ]
