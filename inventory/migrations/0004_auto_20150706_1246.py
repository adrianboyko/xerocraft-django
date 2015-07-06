# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_parkingpermit_ok_to_move'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingpermit',
            name='renewed',
            field=models.DateField(default=datetime.datetime(2015, 7, 6, 19, 46, 30, 824039, tzinfo=utc), help_text='Date/time on which the parking permit was most recently renewed. Initially equal to date created.', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='parkingpermit',
            name='created',
            field=models.DateField(help_text='Date/time on which the parking permit was created.', auto_now_add=True),
        ),
    ]
