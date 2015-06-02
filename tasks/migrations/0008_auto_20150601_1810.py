# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_auto_20150531_1441'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='every_week',
            new_name='every',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='first_week',
            new_name='first',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='fourth_week',
            new_name='fourth',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='last_week',
            new_name='last',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='second_week',
            new_name='second',
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='third_week',
            new_name='third',
        ),
    ]
