# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0014_auto_20150605_1636'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={},
        ),
        migrations.RemoveField(
            model_name='member',
            name='active',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='suspended',
        ),
        migrations.AddField(
            model_name='member',
            name='auth_user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='active',
            field=models.BooleanField(help_text='Additional tasks will be created only when the template is active.', default=True),
        ),
        migrations.AddField(
            model_name='task',
            name='creation_date',
            field=models.DateField(help_text='The date on which this task was originally created, for tracking slippage.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_accepted',
            field=models.NullBooleanField(help_text='If there is a reviewer for this task, the reviewer sets this to true or false once the worker has said that the work is done.', choices=[(True, 'Yes'), (False, 'No'), (None, 'N/A')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='work_done',
            field=models.BooleanField(help_text='The person who does the work sets this to true when the work is completely done.', default=False),
        ),
    ]
