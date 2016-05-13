# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0032_auto_20160512_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseclaimreference',
            name='claim',
            field=models.ForeignKey(help_text='The claim that is paid by the expense transaction.', to='books.ExpenseClaim'),
        ),
    ]
