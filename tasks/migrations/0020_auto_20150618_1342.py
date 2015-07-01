# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0019_auto_20150618_1256'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='auth_user',
        ),
        migrations.RemoveField(
            model_name='worker',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='claim',
            name='claimer',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='eligible_claimants2',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='owner2',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='reviewer2',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='uninterested2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='claimant2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='eligible_claimants2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='owner2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='reviewer2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='uninterested2',
        ),
        migrations.RemoveField(
            model_name='task',
            name='workers2',
        ),
        migrations.RemoveField(
            model_name='tasknote',
            name='author2',
        ),
        migrations.RemoveField(
            model_name='work',
            name='worker2',
        ),
        migrations.DeleteModel(
            name='Worker',
        ),
    ]
