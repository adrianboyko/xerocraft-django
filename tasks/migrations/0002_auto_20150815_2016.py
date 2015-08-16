# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='hours_claimed',
            field=models.DecimalField(max_digits=5, help_text='The actual time claimed, in hours (e.g. 1.25). This is work time, not elapsed time.', decimal_places=2, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tasknote',
            name='status',
            field=models.CharField(choices=[('C', 'Critical'), ('R', 'Resolved'), ('I', 'Informational')], max_length=1, default='N'),
            preserve_default=False,
        ),
    ]
