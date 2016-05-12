# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0031_auto_20160509_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenselineitem',
            name='claim',
            field=models.ForeignKey(help_text='The claim on which this line item appears.', to='books.ExpenseClaim', blank=True, null=True),
        ),
    ]
