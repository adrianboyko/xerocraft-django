# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0025_auto_20160215_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationlineitem',
            name='description',
            field=models.TextField(max_length=2048, help_text='Description, if physical items are being donated. Blank for monetary donation.', null=True, blank=True),
        ),
    ]
