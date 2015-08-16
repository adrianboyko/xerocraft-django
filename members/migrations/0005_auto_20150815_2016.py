# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_visitevent'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='visitevent',
            options={'ordering': ['when']},
        ),
    ]
