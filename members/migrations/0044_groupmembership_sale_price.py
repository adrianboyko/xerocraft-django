# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0043_auto_20160309_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembership',
            name='sale_price',
            field=models.DecimalField(default=0, decimal_places=2, help_text='The price at which this item sold.', max_digits=6),
            preserve_default=False,
        ),
    ]
