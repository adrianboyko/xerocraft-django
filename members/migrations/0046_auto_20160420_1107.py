# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0045_auto_20160320_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='sale_price',
            field=models.DecimalField(default=Decimal('0'), decimal_places=2, max_digits=6, help_text='The price at which this item sold.'),
        ),
    ]
