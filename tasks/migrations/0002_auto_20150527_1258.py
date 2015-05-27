# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='family',
            field=models.ForeignKey(null=True, to='tasks.Member', help_text="If this member is part of a family account then this points to the 'anchor' member for the family."),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='reviewer',
            field=models.ForeignKey(to='tasks.Member', null=True),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='when1',
            field=models.ForeignKey(null=True, to='tasks.DayInNthWeek', help_text='Use when1 XOR when2.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='when2',
            field=models.DateField(help_text='Use when1 XOR when2.', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='claim_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='claimed_by',
            field=models.OneToOneField(related_name='tasks_claimed', null=True, to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='task',
            name='prev_claimed_by',
            field=models.ForeignKey(null=True, to='tasks.Member', related_name='+'),
        ),
        migrations.AlterField(
            model_name='task',
            name='recurring_task_template',
            field=models.ForeignKey(to='tasks.RecurringTaskTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(null=True, to='tasks.Member', related_name='tasks_to_review'),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_accepted',
            field=models.NullBooleanField(),
        ),
    ]
