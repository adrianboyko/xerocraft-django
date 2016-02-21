# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0033_auto_20160220_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='group',
            field=models.ForeignKey(help_text='The associated group membership, if any. Usually none.', to='members.GroupMembership', default=None, null=True, on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='redemption',
            field=models.ForeignKey(help_text='The associated membership gift card redemption, if any. Usually none.', to='members.MembershipGiftCardRedemption', default=None, null=True, on_delete=django.db.models.deletion.PROTECT, blank=True),
        ),
    ]
