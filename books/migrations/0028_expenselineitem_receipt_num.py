# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0027_auto_20160503_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenselineitem',
            name='receipt_num',
            field=models.IntegerField(blank=True, null=True, help_text='The receipt number assigned by the treasurer and written on the receipt.'),
        ),
    ]
