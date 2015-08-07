# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_auto_20150728_2128'),
    ]

    operations = [
        migrations.CreateModel(
            name='VisitEvent',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('when', models.DateTimeField(help_text='Date/time of visit event.', auto_now_add=True)),
                ('event_type', models.CharField(max_length=1, help_text='The type of visit event.', choices=[('A', 'Arrival'), ('P', 'Present'), ('D', 'Departure')])),
                ('sync1', models.BooleanField(default=False, help_text="True if this event has been sync'ed to 'other system #1'")),
                ('who', models.ForeignKey(help_text="The member who's visiting or visited.", to='members.Member', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
    ]
