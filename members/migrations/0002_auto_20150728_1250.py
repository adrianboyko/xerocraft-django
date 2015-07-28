# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagging',
            name='authorizing_member',
            field=models.ForeignKey(related_name='authorized_taggings', to='members.Member', help_text='The member that authorized that the member be tagged.', null=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
