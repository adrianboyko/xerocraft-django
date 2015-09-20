# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20150830_2007'),
        ('tasks', '0010_auto_20150914_1438'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='flexible_dates',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='default_claimant',
            field=models.ForeignKey(to='members.Member', blank=True, on_delete=django.db.models.deletion.SET_NULL, null=True, help_text='Some recurring tasks (e.g. classes) have a default a default claimant (e.g. the instructor).'),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='missed_date_action',
            field=models.CharField(max_length=1, help_text='What should be done if the task is not completed on the scheduled date.', default='S', choices=[('I', "Don't do anything."), ('s', 'Slide the task to the next day.'), ('S', 'Slide task and all later instances to next day.')]),
        ),
        migrations.AddField(
            model_name='task',
            name='missed_date_action',
            field=models.CharField(max_length=1, help_text='What should be done if the task is not completed on the scheduled date.', default='S', choices=[('I', "Don't do anything."), ('s', 'Slide the task to the next day.'), ('S', 'Slide task and all later instances to next day.')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='recurring_task_template',
            field=models.ForeignKey(to='tasks.RecurringTaskTemplate', blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='instances', null=True),
        ),
    ]
