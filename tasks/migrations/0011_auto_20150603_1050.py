# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_auto_20150602_1629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='instructions_note',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='instructions',
            field=models.TextField(max_length=2048, help_text="Instructions that will apply to EVERY task that's created from this template.", blank=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member', blank=True, null=True, help_text='The member that asked for this task to be created or has taken responsibility for its content.', related_name='owned_TaskTemplates'),
        ),
        migrations.AddField(
            model_name='task',
            name='instructions',
            field=models.TextField(max_length=2048, help_text="Instructions that will apply to EVERY task that's created from this template.", blank=True),
        ),
        migrations.AddField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member', blank=True, null=True, help_text='The member that asked for this task to be created or has taken responsibility for its content.', related_name='owned_Tasks'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_claimants',
            field=models.ManyToManyField(to='tasks.Member', related_name='claimable_TaskTemplates', help_text='Anybody listed is eligible to claim the task.', blank=True),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
            field=models.ManyToManyField(to='tasks.Tag', related_name='claimable_TaskTemplates', help_text='Anybody that has one of the listed tags is eligible to claim the task.', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='claimed_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member', blank=True, null=True, related_name='tasks_claimed'),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_claimants',
            field=models.ManyToManyField(to='tasks.Member', related_name='claimable_Tasks', help_text='Anybody listed is eligible to claim the task.', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_tags',
            field=models.ManyToManyField(to='tasks.Tag', related_name='claimable_Tasks', help_text='Anybody that has one of the listed tags is eligible to claim the task.', blank=True),
        ),
        migrations.AlterField(
            model_name='tasknote',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='tasks.Member', blank=True, null=True, help_text='The member who wrote this note.'),
        ),
        migrations.AlterField(
            model_name='tasknote',
            name='content',
            field=models.TextField(max_length=2048, help_text='Anything you want to say about the task. Questions, hints, problems, review feedback, etc.'),
        ),
    ]
