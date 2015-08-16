# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20150815_2016'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='end_time',
            field=models.TimeField(help_text='The time at which the task should end, if any.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='start_time',
            field=models.TimeField(help_text='The time at which the task should being, if any.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='task',
            name='end_time',
            field=models.TimeField(help_text='The time at which the task should end, if any.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='task',
            name='start_time',
            field=models.TimeField(help_text='The time at which the task should being, if any.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='work',
            name='when',
            field=models.DateField(help_text='The date on which the work was done.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='claim',
            name='status',
            field=models.CharField(choices=[('C', 'Current'), ('X', 'Expired'), ('Q', 'Queued')], max_length=1),
        ),
        migrations.AlterField(
            model_name='task',
            name='claimants',
            field=models.ManyToManyField(help_text='The people who say they are going to work on this task.', through='tasks.Claim', related_name='tasks_claimed', to='members.Member'),
        ),
        migrations.AlterField(
            model_name='task',
            name='workers',
            field=models.ManyToManyField(help_text='The people who have actually posted hours against this task.', through='tasks.Work', related_name='tasks_worked', to='members.Member'),
        ),
    ]
