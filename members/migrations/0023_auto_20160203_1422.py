# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0022_auto_20160202_2224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paidmembership',
            name='payment_method',
            field=models.CharField(default='$', help_text='The payment method used.', choices=[('0', 'N/A'), ('$', 'Cash'), ('C', 'Check'), ('G', 'Gift Card'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')], max_length=1),
        ),
    ]
