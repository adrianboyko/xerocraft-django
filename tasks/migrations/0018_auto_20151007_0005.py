# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0017_auto_20151006_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='apr',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='aug',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='dec',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='feb',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='jan',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='jul',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='jun',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='mar',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='may',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='nov',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='oct',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='sep',
            field=models.BooleanField(default=True),
        ),
    ]
