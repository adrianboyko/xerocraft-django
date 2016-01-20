# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0019_auto_20160119_1709'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paidmembership',
            name='protect_from_etl',
        ),
        migrations.AddField(
            model_name='paidmembership',
            name='protected',
            field=models.BooleanField(default=False, help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.'),
        ),
    ]
