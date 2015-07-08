# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_auto_20150706_1333'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parkingpermit',
            options={'ordering': ['renewed']},
        ),
        migrations.AlterModelOptions(
            name='permitscan',
            options={'ordering': ['where', 'when']},
        ),
        migrations.RemoveField(
            model_name='location',
            name='numeric_name',
        ),
        migrations.AddField(
            model_name='location',
            name='x',
            field=models.FloatField(help_text='An ordinate in some coordinate system to help locate the location.', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='y',
            field=models.FloatField(help_text='An ordinate in some coordinate system to help locate the location.', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='z',
            field=models.FloatField(help_text='An ordinate in some coordinate system to help locate the location.', blank=True, null=True),
        ),
    ]
