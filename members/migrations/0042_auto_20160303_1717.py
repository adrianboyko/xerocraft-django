# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import members.models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0041_auto_20160303_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='ctrlid',
            field=models.CharField(help_text="Payment processor's id for this membership if it was part of an online purchase.", max_length=40, default=members.models.next_membership_ctrlid, unique=True),
        ),

    ]
