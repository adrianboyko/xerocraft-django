# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0004_sale_method_detail'),
    ]

    operations = [
        migrations.RenameField(
            model_name='salenote',
            old_name='purchase',
            new_name='sale',
        ),
    ]
