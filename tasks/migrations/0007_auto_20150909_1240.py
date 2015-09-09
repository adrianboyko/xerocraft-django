# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_auto_20150830_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='claim',
            name='date',
            field=models.DateField(auto_now_add=True, help_text='The date on which the member claimed the task.'),
        ),
    ]
