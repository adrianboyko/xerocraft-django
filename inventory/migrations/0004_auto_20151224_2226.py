# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20151224_2159'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='parkingpermit',
            unique_together=set([('owner', 'created', 'short_desc')]),
        ),
    ]
