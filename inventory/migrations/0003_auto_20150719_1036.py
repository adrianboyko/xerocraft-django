# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20150719_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='short_desc',
            field=models.CharField(help_text='A short description/name for the location.', blank=True, null=True, max_length=40),
        ),
    ]
