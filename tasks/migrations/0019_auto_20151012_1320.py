# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0018_auto_20151007_0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='verified_current',
            field=models.BooleanField(help_text='The system has determined that the current claimant will be able to work the task.', default=False),
        ),
        migrations.AlterField(
            model_name='claim',
            name='status',
            field=models.CharField(choices=[('C', 'Current'), ('X', 'Expired'), ('Q', 'Queued'), ('A', 'Abandoned'), ('W', 'Working'), ('D', 'Done')], max_length=1, help_text='The status of this claim.'),
        ),
    ]
