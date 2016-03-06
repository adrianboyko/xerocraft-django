# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import books.models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0012_auto_20160301_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='monetarydonation',
            name='ctrlid',
            field=models.CharField(help_text="Payment processor's id for this donation, if any.", default=books.models.next_monetarydonation_ctrlid, null=True, max_length=40),
        ),
        migrations.AddField(
            model_name='monetarydonation',
            name='protected',
            field=models.BooleanField(help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.', default=False),
        ),
    ]
