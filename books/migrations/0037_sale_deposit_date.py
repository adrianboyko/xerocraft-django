# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0036_auto_20160514_2256'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='deposit_date',
            field=models.DateField(null=True, help_text='The date on which the income from this sale was (or will be) deposited.', blank=True, default=None),
        ),
    ]
