# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0015_auto_20160111_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='paidmembership',
            name='ctrlid',
            field=models.CharField(help_text="Payment processor's id for this payment.", max_length=20, null=True),
        ),
    ]
