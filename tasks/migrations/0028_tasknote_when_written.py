# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0027_auto_20151121_2101'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasknote',
            name='when_written',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 11, 22, 19, 25, 18, 925854, tzinfo=utc), help_text='The date and time when the note was written.'),
            preserve_default=False,
        ),
    ]
