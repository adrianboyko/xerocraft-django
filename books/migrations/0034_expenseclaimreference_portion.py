# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0033_auto_20160513_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenseclaimreference',
            name='portion',
            field=models.DecimalField(null=True, help_text="Leave blank unless you're only paying a portion of the claim.", max_digits=6, default=None, decimal_places=2, blank=True),
        ),
    ]
