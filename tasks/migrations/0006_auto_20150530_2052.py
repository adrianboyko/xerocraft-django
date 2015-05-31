# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_auto_20150529_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='eligible_claimants',
            field=models.ManyToManyField(help_text='Anybody listed is eligible to claim the task', to='tasks.Member', related_name='+'),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
            field=models.ManyToManyField(help_text='Anybody that has one of the listed tags is eligible to claim the task', to='tasks.Tag', related_name='+'),
        ),
        migrations.AddField(
            model_name='task',
            name='eligible_claimants',
            field=models.ManyToManyField(help_text='Anybody listed is eligible to claim the task', to='tasks.Member', related_name='claimable_tasks'),
        ),
        migrations.AddField(
            model_name='task',
            name='eligible_tags',
            field=models.ManyToManyField(help_text='Anybody that has one of the listed tags is eligible to claim the task', to='tasks.Tag', related_name='claimable_tasks'),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(blank=True, help_text='A reviewer that will be copied to instances of the recurring task.', to='tasks.Member', null=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='task',
            name='short_desc',
            field=models.CharField(max_length=40, help_text='A description that will be copied to instances of the recurring task.'),
        ),
    ]
