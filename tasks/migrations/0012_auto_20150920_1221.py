# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_auto_20150920_1151'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='missed_date_action',
            field=models.CharField(default='I', help_text='What should be done if the task is not completed on the scheduled date.', choices=[('I', "Don't do anything."), ('s', 'Slide the task to the next day.'), ('S', 'Slide task and all later instances to next day.')], null=True, blank=True, max_length=1),
        ),
        migrations.AlterField(
            model_name='task',
            name='missed_date_action',
            field=models.CharField(default='I', help_text='What should be done if the task is not completed on the scheduled date.', choices=[('I', "Don't do anything."), ('s', 'Slide the task to the next day.'), ('S', 'Slide task and all later instances to next day.')], null=True, blank=True, max_length=1),
        ),
    ]
