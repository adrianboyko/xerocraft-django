# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0038_auto_20160225_1442'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MembershipReimbursement',
        ),
    ]
