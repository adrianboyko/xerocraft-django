# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import members.models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0020_auto_20160119_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paidmembership',
            name='ctrlid',
            field=models.CharField(max_length=40, default=members.models.next_paidmembership_ctrlid, help_text="Payment processor's id for this payment."),
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='payment_method',
            field=models.CharField(max_length=1, default='$', help_text='The payment method used.', choices=[('$', 'Cash'), ('C', 'Check'), ('G', 'Gift Card'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')]),
        ),
    ]
