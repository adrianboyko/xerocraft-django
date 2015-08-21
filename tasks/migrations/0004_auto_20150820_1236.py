# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_auto_20150815_2109'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recurringtasktemplate',
            options={'ordering': ['short_desc', '-monday', '-tuesday', '-wednesday', '-thursday', '-friday', '-saturday', '-sunday']},
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['scheduled_date', 'start_time']},
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='nag',
            field=models.BooleanField(help_text='If true, people will be encouraged to work the task via email messages.', default=False),
        ),
    ]
