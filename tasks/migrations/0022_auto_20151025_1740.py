# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion

# This file was auto generated but then manually modified to be a set of renames.

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0021_auto_20151021_1700'),
    ]

    operations = [
        migrations.RenameField(
            model_name='claim',
            old_name='task',
            new_name='claimed_task',
        ),
        migrations.RenameField(
            model_name='claim',
            old_name='member',
            new_name='claiming_member',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='max_claimants',
            new_name='max_workders',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='duration',
            new_name='work_duration',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='start_time',
            new_name='work_start_time',
        ),
        migrations.RenameField(
            model_name='task',
            old_name='max_claimants',
            new_name='max_workers',
        ),
        migrations.RenameField(
            model_name='task',
            old_name='duration',
            new_name='work_duration',
        ),
        migrations.RenameField(
            model_name='task',
            old_name='start_time',
            new_name='work_start_time',
        ),
        migrations.RenameField(
            model_name='claim',
            old_name='date',
            new_name='stake_date',
        ),
        migrations.RenameField(
            model_name='claim',
            old_name='elapsed_duration',
            new_name='claimed_duration',
        ),
        migrations.RenameField(
            model_name='claim',
            old_name='elapsed_start_time',
            new_name='claimed_start_time',
        ),

    ]
