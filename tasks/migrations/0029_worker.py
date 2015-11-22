# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_auto_20151012_1240'),
        ('tasks', '0028_tasknote_when_written'),
    ]

    operations = [
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('calendar_token', models.CharField(null=True, blank=True, help_text='Random hex string used to access calendar.', max_length=32)),
                ('last_work_mtd_reported', models.DecimalField(max_digits=5, default=0, help_text='The most recent work MTD total reported to the worker.', decimal_places=2)),
                ('should_include_alarms', models.BooleanField(help_text="Controls whether or not a worker's calendar includes alarms.", default=False)),
                ('should_nag', models.BooleanField(help_text='Controls whether ANY nags should be sent to the worker.', default=False)),
                ('should_report_work_mtd', models.BooleanField(help_text='Controls whether reports should be sent to worker when work MTD changes.', default=False)),
                ('member', models.OneToOneField(related_name='worker', help_text='This must point to the corresponding member.', to='members.Member')),
            ],
        ),
    ]
