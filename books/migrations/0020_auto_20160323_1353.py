# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0019_auto_20160323_1349'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expensetransaction',
            old_name='amount',
            new_name='amount_paid',
        ),
    ]
