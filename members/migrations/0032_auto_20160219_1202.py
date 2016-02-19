# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0031_membership_group'),
    ]

    operations = [
        migrations.RenameField(
            model_name='groupmembership',
            old_name='purchase',
            new_name='sale',
        ),
        migrations.RenameField(
            model_name='membership',
            old_name='purchase',
            new_name='sale',
        ),
        migrations.RenameField(
            model_name='membershipgiftcardreference',
            old_name='purchase',
            new_name='sale',
        ),
    ]
