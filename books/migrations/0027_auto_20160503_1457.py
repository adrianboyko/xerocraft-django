# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0026_auto_20160420_1107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenselineitem',
            name='exp',
            field=models.ForeignKey(help_text='The expense transaction on which this line item appears.', null=True, to='books.ExpenseTransaction', blank=True),
        ),
    ]
