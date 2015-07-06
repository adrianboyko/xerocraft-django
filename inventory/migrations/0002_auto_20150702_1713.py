# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='location',
            options={'ordering': ['short_desc']},
        ),
        migrations.AddField(
            model_name='location',
            name='numeric_name',
            field=models.IntegerField(default=1, help_text='A number designating the location'),
            preserve_default=False,
        ),
    ]
