# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_calendarsettings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calendarsettings',
            options={'verbose_name_plural': 'Calendar settings'},
        ),
        migrations.AlterModelOptions(
            name='recurringtasktemplate',
            options={'ordering': ['short_desc', '-sunday', '-monday', '-tuesday', '-wednesday', '-thursday', '-friday', '-saturday']},
        ),
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.CharField(default='W', choices=[('W', 'Workable'), ('R', 'Reviewable'), ('D', 'Done'), ('C', 'Canceled')], help_text='The status of this task.', max_length=1),
        ),
    ]
