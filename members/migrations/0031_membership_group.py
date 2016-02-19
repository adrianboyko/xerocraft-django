# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0030_groupmembership'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='group',
            field=models.ForeignKey(to='members.GroupMembership', on_delete=django.db.models.deletion.PROTECT, help_text='The associated group membership, if any. Usually none.', blank=True, null=True),
        ),
    ]
