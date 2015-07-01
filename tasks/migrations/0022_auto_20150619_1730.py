# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0021_auto_20150618_1512'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='membership_card_seq',
        ),
        migrations.AddField(
            model_name='member',
            name='membership_card_str',
            field=models.CharField(null=True, max_length=32, help_text='A random urlsafe base64 string, 32 characters long.', blank=True),
        ),
    ]
