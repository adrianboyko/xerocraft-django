# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0031_remove_worker_last_work_mtd_reported'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='last_work_mtd_reported',
            field=models.DurationField(default=datetime.timedelta(0), help_text='The most recent work MTD total reported to the worker.'),
        ),
    ]
