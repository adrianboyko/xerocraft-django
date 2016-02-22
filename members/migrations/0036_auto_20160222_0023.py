# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0035_auto_20160221_2347'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membernote',
            name='task',
        ),
        migrations.AddField(
            model_name='membernote',
            name='member',
            field=models.ForeignKey(to='members.Member', help_text='The member to which this note pertains.', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='membership',
            name='group',
            field=models.ForeignKey(null=True, to='members.GroupMembership', help_text='The associated group membership, if any. Usually none.', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='member',
            field=models.ForeignKey(null=True, to='members.Member', help_text='The member to whom this membership applies.', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='redemption',
            field=models.ForeignKey(null=True, to='members.MembershipGiftCardRedemption', help_text='The associated membership gift card redemption, if any. Usually none.', default=None, blank=True),
        ),
    ]
