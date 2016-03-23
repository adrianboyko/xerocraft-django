# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0020_auto_20160323_1353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseclaimreference',
            name='claim',
            field=models.OneToOneField(help_text='The claim that is paid by the expense transaction.', to='books.ExpenseClaim'),
        ),
        migrations.AlterField(
            model_name='expensetransaction',
            name='recipient_email',
            field=models.EmailField(help_text='Email address of person/organization paid.', blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='expensetransaction',
            name='recipient_name',
            field=models.CharField(help_text="Name of person/organization paid. Not req'd if account was linked, above.", blank=True, max_length=40),
        ),
    ]
