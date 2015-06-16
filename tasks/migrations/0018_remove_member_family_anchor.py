# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0017_auto_20150615_2305'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='family_anchor',
        ),
    ]
