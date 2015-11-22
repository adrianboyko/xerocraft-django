# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0025_auto_20151027_2109'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='work',
            options={'verbose_name_plural': 'Work'},
        ),
        migrations.AlterField(
            model_name='tasknote',
            name='task',
            field=models.ForeignKey(to='tasks.Task', related_name='notes'),
        ),
    ]
