# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0035_auto_20160514_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensetransaction',
            name='payment_method',
            field=models.CharField(help_text='The payment method used.', choices=[('$', 'Cash'), ('C', 'Check'), ('X', 'Electronic')], default='$', max_length=1),
        ),
    ]
