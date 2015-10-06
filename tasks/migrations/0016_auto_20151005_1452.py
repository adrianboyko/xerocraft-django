# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_auto_20151003_1034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='missed_date_action',
            field=models.CharField(default='I', choices=[('I', "Don't do anything."), ('S', 'Slide task and all later instances forward.')], help_text='What should be done if the task is not completed by the deadline date.', null=True, max_length=1, blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='missed_date_action',
            field=models.CharField(default='I', choices=[('I', "Don't do anything."), ('S', 'Slide task and all later instances forward.')], help_text='What should be done if the task is not completed by the deadline date.', null=True, max_length=1, blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(default='A', max_length=1, choices=[('A', 'Active'), ('R', 'Reviewable'), ('D', 'Done'), ('C', 'Canceled')], help_text='The status of this task.'),
        ),
    ]
