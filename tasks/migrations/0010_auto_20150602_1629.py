# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_recurringtasktemplate_instructions_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(blank=True, to='tasks.Tag'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_claimants',
            field=models.ManyToManyField(related_name='+', blank=True, help_text='Anybody listed is eligible to claim the task.', to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
            field=models.ManyToManyField(related_name='+', blank=True, help_text='Anybody that has one of the listed tags is eligible to claim the task.', to='tasks.Tag'),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_claimants',
            field=models.ManyToManyField(related_name='claimable_tasks', blank=True, help_text='Anybody listed is eligible to claim the task.', to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_tags',
            field=models.ManyToManyField(related_name='claimable_tasks', blank=True, help_text='Anybody that has one of the listed tags is eligible to claim the task.', to='tasks.Tag'),
        ),
    ]
