# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0036_nag_claims'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnavailableDates',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('start_date', models.DateField(help_text='The first date (inclusive) on which the person will be unavailable.')),
                ('end_date', models.DateField(help_text='The last date (inclusive) on which the person will be unavailable.')),
                ('who', models.ForeignKey(blank=True, help_text='The member who wrote this note.', to='tasks.Worker', null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
        ),
    ]
