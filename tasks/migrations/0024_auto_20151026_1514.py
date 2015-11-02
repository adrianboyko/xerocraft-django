# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0023_fix_typo_in_0022'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['scheduled_date', 'work_start_time']},
        ),
        migrations.RemoveField(
            model_name='claim',
            name='hours_claimed',
        ),
        migrations.RemoveField(
            model_name='claim',
            name='verified_current',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='work_estimate',
        ),
        migrations.RemoveField(
            model_name='task',
            name='work_estimate',
        ),
        migrations.RemoveField(
            model_name='work',
            name='when',
        ),
        migrations.RemoveField(
            model_name='work',
            name='work_effort',
        ),
        migrations.RemoveField(
            model_name='work',
            name='work_start_time',
        ),
        migrations.AddField(
            model_name='claim',
            name='date_verified',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='max_work',
            field=models.DurationField(help_text='The max total amount of hours that can be claimed/worked for this task.', default=datetime.timedelta(hours=99)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='max_work',
            field=models.DurationField(help_text='The max total amount of hours that can be claimed/worked for this task.', default=datetime.timedelta(hours=99)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='work',
            name='work_date',
            field=models.DateField(help_text='The date on which the work was done.', default=datetime.datetime(2015, 10, 26, 22, 13, 7, 788191, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='claim',
            name='claimed_duration',
            field=models.DurationField(help_text='The amount of work the member plans to do on the task.'),
        ),
        migrations.AlterField(
            model_name='claim',
            name='claimed_start_time',
            field=models.TimeField(null=True, blank=True, help_text='If the task specifies a start time and duration, this must fall within that time span. Otherwise it should be blank.'),
        ),
        migrations.AlterField(
            model_name='claim',
            name='stake_date',
            field=models.DateField(auto_now_add=True, help_text='The date on which the member staked this claim.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='max_workers',
            field=models.IntegerField(help_text='The maximum number of members that can claim/work the task, often 1.', default=1),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='work_duration',
            field=models.DurationField(help_text='Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='work_start_time',
            field=models.TimeField(null=True, blank=True, help_text="The time at which work on the task must begin. If time doesn't matter, leave blank."),
        ),
        migrations.AlterField(
            model_name='task',
            name='max_workers',
            field=models.IntegerField(help_text='The maximum number of members that can claim/work the task, often 1.', default=1),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_duration',
            field=models.DurationField(help_text='Used with work_start_time to specify the time span over which work must occur. <br/>If work_start_time is blank then this should also be blank.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_start_time',
            field=models.TimeField(null=True, blank=True, help_text="The time at which work on the task must begin. If time doesn't matter, leave blank."),
        ),
        migrations.AlterField(
            model_name='work',
            name='claim',
            field=models.ForeignKey(to='tasks.Claim', on_delete=django.db.models.deletion.PROTECT, help_text='The claim against which the work is being reported.'),
        ),
        migrations.AlterField(
            model_name='work',
            name='work_duration',
            field=models.DurationField(help_text='The amount of time the member spent working.'),
        ),
    ]
