# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0032_worker_last_work_mtd_reported'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='worker',
            options={'ordering': ['member__auth_user__first_name', 'member__auth_user__last_name']},
        ),
    ]
