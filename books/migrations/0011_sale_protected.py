# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0010_auto_20160227_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='protected',
            field=models.BooleanField(default=False, help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.'),
        ),
    ]
