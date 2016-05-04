# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0048_auto_20160503_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagging',
            name='authorizing_member',
            field=models.ForeignKey(to='members.Member', blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authorized_taggings', help_text='The member that authorized that the member be tagged.', null=True),
        ),
    ]
