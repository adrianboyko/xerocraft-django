# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0016_paidmembership_ctrlid'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='paidmembership',
            unique_together=set([('payment_method', 'ctrlid')]),
        ),
    ]
