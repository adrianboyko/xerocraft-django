# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import books.models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0014_auto_20160304_2237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monetarydonation',
            name='ctrlid',
            field=models.CharField(help_text="Payment processor's id for this donation, if any.", default=books.models.next_monetarydonation_ctrlid, unique=True, max_length=40),
        ),
    ]
