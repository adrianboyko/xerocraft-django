# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_auto_20150706_1246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parkingpermit',
            name='renewed',
            field=models.DateField(help_text='Date/time on which the parking permit was most recently renewed. Initially equal to date created.', default=datetime.date.today),
        ),
    ]
