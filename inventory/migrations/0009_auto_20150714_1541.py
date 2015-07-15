# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_auto_20150714_1505'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parkingpermit',
            options={'ordering': ['owner', 'created']},
        ),
        migrations.RemoveField(
            model_name='parkingpermit',
            name='renewed',
        ),
    ]
