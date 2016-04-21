# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0025_auto_20160323_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='send_receipt',
            field=models.BooleanField(default=True, help_text='(Re)send a receipt to the donor. Note: Will send at night.'),
        ),
        migrations.AlterField(
            model_name='expenselineitem',
            name='exp',
            field=models.ForeignKey(null=True, to='books.ExpenseTransaction', help_text='The expense transaction on which this line item appears.'),
        ),
    ]
