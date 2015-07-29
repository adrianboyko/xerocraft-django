# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_auto_20150728_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='tagging',
            name='date_tagged',
            field=models.DateTimeField(default=datetime.datetime(2015, 7, 29, 4, 28, 8, 373347, tzinfo=utc), auto_now_add=True, help_text='Date/time on which the member was tagged.'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='tagging',
            unique_together=set([('tagged_member', 'tag')]),
        ),
    ]
