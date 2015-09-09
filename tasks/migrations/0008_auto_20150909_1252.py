# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_auto_20150909_1240'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='claim',
            unique_together=set([('member', 'task')]),
        ),
    ]
