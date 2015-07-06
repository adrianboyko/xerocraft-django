# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20150702_1713'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingpermit',
            name='ok_to_move',
            field=models.BooleanField(help_text='Is it OK to carefully move the item to another location, if necessary?', default=True),
        ),
    ]
