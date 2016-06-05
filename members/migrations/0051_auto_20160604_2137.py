# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0050_wifimacdetected'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wifimacdetected',
            options={'verbose_name_plural': 'Wifi MACs detected', 'verbose_name': 'Wifi MAC detected'},
        ),
    ]
