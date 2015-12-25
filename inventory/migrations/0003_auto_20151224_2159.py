# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_auto_20151012_1240'),
        ('inventory', '0002_auto_20151223_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingpermit',
            name='approving_member',
            field=models.ForeignKey(blank=True, null=True, to='members.Member', related_name='permits_approved', help_text='The paying member who approved the parking of this item.', on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='parkingpermit',
            name='ok_to_move',
            field=models.BooleanField(help_text='Is it OK to carefully move the item to another location without involving owner?', default=True),
        ),
        migrations.AlterField(
            model_name='parkingpermit',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='members.Member', related_name='permits_owned', help_text='The member who owns the parked item.'),
        ),
    ]
