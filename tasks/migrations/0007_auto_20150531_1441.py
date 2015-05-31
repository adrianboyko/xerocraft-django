# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_auto_20150530_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='suspended',
            field=models.BooleanField(help_text='Additional tasks will not be created from this template while it is suspended.', default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='scheduled_date',
            field=models.DateField(null=True, help_text='If appropriate, set a date on which the task must be performed.', blank=True),
        ),
    ]
