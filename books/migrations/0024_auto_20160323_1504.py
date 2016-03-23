# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0023_auto_20160323_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenselineitem',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='The dollar amount for this line item.', max_digits=6),
        ),
        migrations.AlterField(
            model_name='expenselineitem',
            name='description',
            field=models.CharField(help_text='A brief description of this line item.', max_length=80),
        ),
        migrations.AlterField(
            model_name='expenselineitem',
            name='expense_date',
            field=models.DateField(help_text='The date on which the expense was incurred.'),
        ),
    ]
