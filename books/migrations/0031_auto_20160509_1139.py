# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0030_auto_20160508_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='expenseclaim',
            name='claim_date',
        ),
        migrations.AddField(
            model_name='expenseclaim',
            name='submit',
            field=models.BooleanField(help_text='(Re)submit the claim for processing and reimbursement.', default=False),
        ),
        migrations.AddField(
            model_name='expenseclaim',
            name='when_submitted',
            field=models.DateField(help_text='The date on which the claim was most recently (re)submitted for reimbursement.', default=None, blank=True, null=True),
        ),
    ]
