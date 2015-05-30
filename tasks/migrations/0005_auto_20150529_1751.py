# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_auto_20150529_1135'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='family',
        ),
        migrations.AddField(
            model_name='member',
            name='family_anchor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text="If this member is part of a family account then this points to the 'anchor' member for the family.", to='tasks.Member', null=True, related_name='family_members'),
        ),
    ]
