# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0040_snippet'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='uninterested',
        ),
        migrations.RemoveField(
            model_name='task',
            name='uninterested',
        ),
        migrations.AlterField(
            model_name='claim',
            name='status',
            field=models.CharField(max_length=1, choices=[('C', 'Current'), ('X', 'Expired'), ('Q', 'Queued'), ('A', 'Abandoned'), ('W', 'Working'), ('D', 'Done'), ('U', 'Uninterested')], help_text='The status of this claim.'),
        ),
        migrations.AlterField(
            model_name='snippet',
            name='name',
            field=models.CharField(max_length=40, validators=[django.core.validators.RegexValidator('^[-a-zA-Z0-1]+$', code='invalid_name', message='Name must only contain letters, numbers, and dashes.')], help_text='The name of the snippet.'),
        ),
    ]
