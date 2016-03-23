# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0022_auto_20160323_1427'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenselineitem',
            name='claim',
            field=models.ForeignKey(null=True, help_text='The claim on which this line item appears.', to='books.ExpenseClaim'),
        ),
        migrations.AlterField(
            model_name='expenselineitem',
            name='exp',
            field=models.ForeignKey(null=True, help_text='The claim on which this line item appears.', to='books.ExpenseTransaction'),
        ),
    ]
