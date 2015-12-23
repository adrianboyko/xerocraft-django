# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_auto_20151012_1240'),
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parkingpermit',
            options={'ordering': ['owner', 'pk', 'created']},
        ),
        migrations.AlterModelOptions(
            name='permitrenewal',
            options={'ordering': ['permit', 'when']},
        ),
        migrations.AddField(
            model_name='permitscan',
            name='who',
            field=models.ForeignKey(to='members.Member', help_text='The member who scanned the permit.', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
        migrations.AlterField(
            model_name='permitrenewal',
            name='when',
            field=models.DateField(help_text='Date on which the parking permit was renewed.'),
        ),
    ]
