# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_auto_20150820_1236'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='priority',
            field=models.CharField(max_length=1, default='M', choices=[('H', 'High'), ('M', 'Medium'), ('L', 'Low')], help_text='The priority of the task, compared to other tasks.'),
        ),
        migrations.AddField(
            model_name='task',
            name='nag',
            field=models.BooleanField(default=False, help_text='If true, people will be encouraged to work the task via email messages.'),
        ),
        migrations.AddField(
            model_name='task',
            name='priority',
            field=models.CharField(max_length=1, default='M', choices=[('H', 'High'), ('M', 'Medium'), ('L', 'Low')], help_text='The priority of the task, compared to other tasks.'),
        ),
    ]
