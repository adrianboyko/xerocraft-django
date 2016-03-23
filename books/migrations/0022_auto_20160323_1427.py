# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0021_auto_20160323_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseLineItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('description', models.CharField(blank=True, help_text='A brief description of this line item.', max_length=80)),
                ('expense_date', models.DateField(help_text='The date on which the expense was incurred, from the receipt.')),
                ('amount', models.DecimalField(max_digits=6, help_text='The dollar amount for this line item, from the receipt.', decimal_places=2)),
                ('account', models.ForeignKey(help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.", to='books.Account')),
                ('claim', models.ForeignKey(help_text='The claim on which this line item appears.', to='books.ExpenseClaim')),
                ('exp', models.ForeignKey(help_text='The claim on which this line item appears.', to='books.ExpenseTransaction')),
            ],
        ),
        migrations.RemoveField(
            model_name='expenseclaimlineitem',
            name='account',
        ),
        migrations.RemoveField(
            model_name='expenseclaimlineitem',
            name='claim',
        ),
        migrations.DeleteModel(
            name='ExpenseClaimLineItem',
        ),
    ]
