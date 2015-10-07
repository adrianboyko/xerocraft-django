# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0016_auto_20151005_1452'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='task',
            unique_together=set([('scheduled_date', 'short_desc')]),
        ),
    ]
