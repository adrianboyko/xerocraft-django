# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0022_auto_20151025_1740'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='max_workders',
            new_name='max_workers',
        ),
    ]
