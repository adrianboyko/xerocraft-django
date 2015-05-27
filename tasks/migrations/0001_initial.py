# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DayInNthWeek',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('first', models.BooleanField(default=False)),
                ('second', models.BooleanField(default=False)),
                ('third', models.BooleanField(default=False)),
                ('fourth', models.BooleanField(default=False)),
                ('last', models.BooleanField(default=False, help_text='Some months have a fifth Monday, or Tuesday, ...')),
                ('day_of_week', models.CharField(max_length=3, choices=[('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday')])),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=40)),
                ('last_name', models.CharField(max_length=40)),
                ('user_id', models.CharField(max_length=40, help_text='The user-id the member uses to sign in at Xerocraft.')),
                ('family', models.ForeignKey(to='tasks.Member', help_text="If this member is part of a family account then this points to the 'anchor' member for the family.")),
            ],
        ),
        migrations.CreateModel(
            name='RecurringTaskTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('short_desc', models.CharField(max_length=40)),
                ('long_desc', models.TextField(max_length=500)),
                ('first_instance_date', models.DateField()),
                ('when2', models.DateField(help_text='Use when1 XOR when2.')),
                ('reviewer', models.ForeignKey(to='tasks.Member')),
                ('when1', models.ForeignKey(to='tasks.DayInNthWeek', help_text='Use when1 XOR when2.')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('short_desc', models.CharField(max_length=40)),
                ('long_desc', models.TextField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('short_desc', models.CharField(max_length=40)),
                ('long_desc', models.TextField(max_length=500)),
                ('claim_date', models.DateField()),
                ('work_done', models.BooleanField(default=False)),
                ('work_accepted', models.BooleanField(default=False)),
                ('claimed_by', models.OneToOneField(to='tasks.Member', related_name='tasks_claimed')),
                ('prev_claimed_by', models.ForeignKey(related_name='+', to='tasks.Member')),
                ('recurring_task_template', models.ForeignKey(to='tasks.RecurringTaskTemplate')),
                ('reviewer', models.ForeignKey(related_name='tasks_to_review', to='tasks.Member')),
            ],
        ),
        migrations.AddField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(to='tasks.Tag'),
        ),
    ]
