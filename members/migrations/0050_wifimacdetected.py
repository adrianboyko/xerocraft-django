# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0049_auto_20160503_1146'),
    ]

    operations = [
        migrations.CreateModel(
            name='WifiMacDetected',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('when', models.DateTimeField(default=django.utils.timezone.now, help_text='Date/time when MAC was noticed to be present.')),
                ('mac', models.CharField(max_length=12, help_text='A MAC address as 12 hex digits.')),
            ],
        ),
    ]
