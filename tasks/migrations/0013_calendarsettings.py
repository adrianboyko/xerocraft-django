# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20150830_2007'),
        ('tasks', '0012_auto_20150920_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('token', models.CharField(max_length=32, help_text='Random hex string used to access calendar.')),
                ('include_alarms', models.BooleanField(help_text='The member can control whether or not their calendar includes alarms.', default=True)),
                ('who', models.ForeignKey(help_text='Member the calendar corresponds to.', to='members.Member')),
            ],
        ),
    ]
