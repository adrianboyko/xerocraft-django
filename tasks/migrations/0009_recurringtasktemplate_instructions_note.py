# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_auto_20150601_1810'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='instructions_note',
            field=models.ForeignKey(help_text="Provide instructions that will apply to <b>every</b> task that's created from this template.", blank=True, to='tasks.TaskNote', null=True),
        ),
    ]
