# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_auto_20150603_1050'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={'ordering': ['first_name', 'last_name']},
        ),
        migrations.AlterModelOptions(
            name='recurringtasktemplate',
            options={'ordering': ['short_desc']},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['short_desc']},
        ),
        migrations.AddField(
            model_name='member',
            name='active',
            field=models.BooleanField(default=True, help_text='Systems should ignore this member, to the extent possible.'),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='on_demand',
            field=models.NullBooleanField(default=False, help_text='If selected, tasks will only be scheduled on demand (subject to the delay constraint), otherwise tasks will be automatically scheduled after delay.'),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='repeat_delay',
            field=models.SmallIntegerField(blank=True, help_text='Minimum number of days between recurrences, e.g. 14 for every two weeks.', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='work_actual',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The actual time worked, in hours (e.g. 1.25). This is work time, not elapsed time.', null=True, max_digits=5),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_claimants',
            field=models.ManyToManyField(to='tasks.Member', blank=True, related_name='claimable_TaskTemplates', help_text='Anybody chosen is eligible to claim the task.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
            field=models.ManyToManyField(to='tasks.Tag', blank=True, related_name='claimable_TaskTemplates', help_text='Anybody that has one of the chosen tags is eligible to claim the task.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='every',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='first',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='fourth',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='friday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='instructions',
            field=models.TextField(max_length=2048, blank=True, help_text='Instructions for completing the task.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='last',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='monday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='reviewer',
            field=models.ForeignKey(to='tasks.Member', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='If required, a member who will review the work once its completed.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='saturday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='second',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='short_desc',
            field=models.CharField(max_length=40, help_text='A short description/name for the task.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='sunday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='third',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='thursday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='tuesday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='wednesday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='work_estimate',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='An estimate of how much work this tasks requires, in hours (e.g. 1.25). This is work time, not elapsed time.', null=True, max_digits=5),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_claimants',
            field=models.ManyToManyField(to='tasks.Member', blank=True, related_name='claimable_Tasks', help_text='Anybody chosen is eligible to claim the task.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='eligible_tags',
            field=models.ManyToManyField(to='tasks.Tag', blank=True, related_name='claimable_Tasks', help_text='Anybody that has one of the chosen tags is eligible to claim the task.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='instructions',
            field=models.TextField(max_length=2048, blank=True, help_text='Instructions for completing the task.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(to='tasks.Member', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, help_text='If required, a member who will review the work once its completed.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='short_desc',
            field=models.CharField(max_length=40, help_text='A short description/name for the task.'),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_estimate',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='An estimate of how much work this tasks requires, in hours (e.g. 1.25). This is work time, not elapsed time.', null=True, max_digits=5),
        ),
    ]
