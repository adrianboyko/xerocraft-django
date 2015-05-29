# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_auto_20150528_1213'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='family',
            field=models.ForeignKey(help_text="If this member is part of a family account then this points to the 'anchor' member for the family.", on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.Member', blank=True),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='reviewer',
            field=models.ForeignKey(help_text='A reviewer that will be copied to instances of the recurring task.', on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.Member', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='claim_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='claimed_by',
            field=models.ForeignKey(related_name='tasks_claimed', null=True, to='tasks.Member', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='deadline',
            field=models.DateField(help_text='If appropriate, specify a deadline by which the task must be completed.', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='depends_on',
            field=models.ManyToManyField(to='tasks.Task', help_text='If appropriate, specify what tasks must be completed before this one can start.', related_name='prerequisite_for'),
        ),
        migrations.AlterField(
            model_name='task',
            name='prev_claimed_by',
            field=models.ForeignKey(related_name='+', null=True, to='tasks.Member', blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='task',
            name='recurring_task_template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.RecurringTaskTemplate', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(help_text='If required, a member who will review the completed work and either accept or reject it.', related_name='tasks_to_review', null=True, to='tasks.Member', blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='tasknote',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.Member', blank=True),
        ),
    ]
