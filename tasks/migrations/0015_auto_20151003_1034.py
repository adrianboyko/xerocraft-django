# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_auto_20151002_1646'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='work_accepted',
        ),
        migrations.RemoveField(
            model_name='task',
            name='work_done',
        ),
    ]
