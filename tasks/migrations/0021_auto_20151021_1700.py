# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0020_auto_20151021_0017'),
    ]

    operations = [
        migrations.RenameField(
            model_name='work',
            old_name='hours',
            new_name='work_effort',
        ),
        migrations.RemoveField(
            model_name='task',
            name='workers',
        ),
        migrations.RemoveField(
            model_name='work',
            name='task',
        ),
        migrations.RemoveField(
            model_name='work',
            name='worker',
        ),
        migrations.AddField(
            model_name='work',
            name='claim',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='tasks.Claim', help_text='The claim against which the work was done.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='work',
            name='work_duration',
            field=models.DurationField(blank=True, null=True, help_text='The elapsed time the member plans to work.'),
        ),
        migrations.AddField(
            model_name='work',
            name='work_start_time',
            field=models.TimeField(blank=True, null=True, help_text='The clock time at which the member plans to start work.'),
        ),
    ]
