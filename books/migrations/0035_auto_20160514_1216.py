# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0034_expenseclaimreference_portion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensetransaction',
            name='payment_date',
            field=models.DateField(blank=True, null=True, default=None, help_text='The date on which the expense was paid (use bank statement date). Blank if not yet paid or statement not yet received. Best guess if paid but exact date not known.'),
        ),
    ]
