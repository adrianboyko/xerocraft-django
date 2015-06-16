# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0016_auto_20150611_1736'),
    ]

    operations = [
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('C', 'Current Claim'), ('X', 'Expired Claim'), ('Q', 'Queued Claim')], max_length=1)),
                ('member', models.ForeignKey(to='tasks.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('hours', models.DecimalField(help_text='The actual time worked, in hours (e.g. 1.25). This is work time, not elapsed time.', max_digits=5, decimal_places=2)),
            ],
        ),
        migrations.RemoveField(
            model_name='task',
            name='claim_date',
        ),
        migrations.RemoveField(
            model_name='task',
            name='claimed_by',
        ),
        migrations.RemoveField(
            model_name='task',
            name='prev_claimed_by',
        ),
        migrations.RemoveField(
            model_name='task',
            name='work_actual',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='max_claimants',
            field=models.IntegerField(help_text='The maximum number of members that can simultaneously claim/work the task, often 1.', default=1),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='uninterested',
            field=models.ManyToManyField(help_text='Members that are not interested in this item.', blank=True, to='tasks.Member', related_name='uninteresting_TaskTemplates'),
        ),
        migrations.AddField(
            model_name='task',
            name='max_claimants',
            field=models.IntegerField(help_text='The maximum number of members that can simultaneously claim/work the task, often 1.', default=1),
        ),
        migrations.AddField(
            model_name='task',
            name='uninterested',
            field=models.ManyToManyField(help_text='Members that are not interested in this item.', blank=True, to='tasks.Member', related_name='uninteresting_Tasks'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='reviewer',
            field=models.ForeignKey(help_text='If required, a member who will review the work once its completed.', related_name='reviewableTaskTemplates', on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.Member', blank=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(help_text='If required, a member who will review the work once its completed.', related_name='reviewableTasks', on_delete=django.db.models.deletion.SET_NULL, null=True, to='tasks.Member', blank=True),
        ),
        migrations.AddField(
            model_name='work',
            name='task',
            field=models.ForeignKey(help_text='The task that was worked.', to='tasks.Task'),
        ),
        migrations.AddField(
            model_name='work',
            name='worker',
            field=models.ForeignKey(help_text='Member that did work toward completing task.', to='tasks.Member'),
        ),
        migrations.AddField(
            model_name='claim',
            name='task',
            field=models.ForeignKey(to='tasks.Task'),
        ),
        migrations.AddField(
            model_name='task',
            name='claimants',
            field=models.ManyToManyField(related_name='tasks_claimed', to='tasks.Member', through='tasks.Claim'),
        ),
        migrations.AddField(
            model_name='task',
            name='workers',
            field=models.ManyToManyField(related_name='tasks_worked', to='tasks.Member', through='tasks.Work'),
        ),
    ]
