# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0030_auto_20151122_1721'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='last_work_mtd_reported',
        ),
    ]
