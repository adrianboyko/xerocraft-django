# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0025_auto_20150702_1643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(related_name='members', to='tasks.Tag', blank=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(unique=True, max_length=40, help_text='A short name for the tag.'),
        ),
    ]
