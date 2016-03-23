# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import books.models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0024_auto_20160323_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otheritem',
            name='ctrlid',
            field=models.CharField(unique=True, max_length=40, default=books.models.next_otheritem_ctrlid, help_text="Payment processor's id for this donation, if any."),
        ),
    ]
