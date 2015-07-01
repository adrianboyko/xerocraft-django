# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0022_auto_20150619_1730'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='membership_card_str',
        ),
        migrations.AddField(
            model_name='member',
            name='membership_card_md5',
            field=models.CharField(null=True, blank=True, max_length=32, help_text='MD5 checksum of the random urlsafe base64 string on the membership card.'),
        ),
        migrations.AddField(
            model_name='member',
            name='membership_card_when',
            field=models.DateTimeField(null=True, blank=True, help_text='Date/time on which the membership card was created.'),
        ),
    ]
