# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_auto_20150815_2016'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={'ordering': ['auth_user__first_name', 'auth_user__last_name']},
        ),
    ]
