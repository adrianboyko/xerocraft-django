# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0029_worker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calendarsettings',
            name='who',
        ),
        migrations.DeleteModel(
            name='CalendarSettings',
        ),
    ]
