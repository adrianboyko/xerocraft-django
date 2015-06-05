# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0012_auto_20150605_1434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='active',
            field=models.BooleanField(help_text='If selected, systems will ignore this member, to the extent possible.', default=True),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_claimants',
            field=models.ManyToManyField(help_text='Anybody chosen is eligible to claim the task.<br/>', to='tasks.Member', blank=True, related_name='claimable_TaskTemplates'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
            field=models.ManyToManyField(help_text='Anybody that has one of the chosen tags is eligible to claim the task.<br/>', to='tasks.Tag', blank=True, related_name='claimable_TaskTemplates'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='on_demand',
            field=models.NullBooleanField(help_text='If selected, tasks will only be scheduled on demand, subject to the delay constraint.<br/>Otherwise tasks will be automatically scheduled after delay.', default=None),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='owner',
            field=models.ForeignKey(help_text='The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.', blank=True, related_name='owned_TaskTemplates', null=True, on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='work_estimate',
            field=models.DecimalField(null=True, help_text='An estimate of how much work this tasks requires, in hours (e.g. 1.25).<br/>This is work time, not elapsed time.', blank=True, max_digits=5, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_claimants',
            field=models.ManyToManyField(help_text='Anybody chosen is eligible to claim the task.<br/>', to='tasks.Member', blank=True, related_name='claimable_Tasks'),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_tags',
            field=models.ManyToManyField(help_text='Anybody that has one of the chosen tags is eligible to claim the task.<br/>', to='tasks.Tag', blank=True, related_name='claimable_Tasks'),
        ),
        migrations.AlterField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(help_text='The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.', blank=True, related_name='owned_Tasks', null=True, on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_estimate',
            field=models.DecimalField(null=True, help_text='An estimate of how much work this tasks requires, in hours (e.g. 1.25).<br/>This is work time, not elapsed time.', blank=True, max_digits=5, decimal_places=2),
        ),
    ]
