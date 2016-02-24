# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0036_auto_20160222_0023'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscoveryMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30, unique=True, help_text='The name of some means by which people learn about our organization.')),
                ('order', models.IntegerField(unique=True, help_text='These values define the order in which the discovery methods should be presented to users.', default=None)),
            ],
        ),
    ]
