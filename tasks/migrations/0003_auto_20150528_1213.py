# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20150527_1258'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskNote',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('content', models.TextField(verbose_name=2048, help_text='Anything you want to say about the task. Instructions, hints, requirements, review feedback, etc.')),
                ('author', models.ForeignKey(to='tasks.Member')),
            ],
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='first_instance_date',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='long_desc',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='when1',
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='when2',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='long_desc',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='short_desc',
        ),
        migrations.RemoveField(
            model_name='task',
            name='long_desc',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='every_week',
            field=models.BooleanField(help_text='Task recur every week', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='first_week',
            field=models.BooleanField(help_text='Task will recur on first weekday in the month.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='fourth_week',
            field=models.BooleanField(help_text='Task will recur on fourth weekday in the month.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='friday',
            field=models.BooleanField(help_text='Task will recur on Friday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='last_week',
            field=models.BooleanField(help_text='Task will recur on last weekday in the month. This will be 4th or 5th weekday, depending on calendar.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='monday',
            field=models.BooleanField(help_text='Task will recur on Monday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='saturday',
            field=models.BooleanField(help_text='Task will recur a Saturday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='second_week',
            field=models.BooleanField(help_text='Task will recur on second weekday in the month.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='start_date',
            field=models.DateField(default=datetime.datetime(2015, 5, 28, 19, 12, 41, 523462, tzinfo=utc), help_text='Choose a date for the first instance of the recurring task.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='sunday',
            field=models.BooleanField(help_text='Task will recur a Sunday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='third_week',
            field=models.BooleanField(help_text='Task will recur on third weekday in the month.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='thursday',
            field=models.BooleanField(help_text='Task will recur on Thursday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='tuesday',
            field=models.BooleanField(help_text='Task will recur on Tuesday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='wednesday',
            field=models.BooleanField(help_text='Task will recur on Wednesday.', default=False),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='work_estimate',
            field=models.IntegerField(default=0, help_text='Provide an estimate of how much work this tasks requires, in minutes. This is work time, not elapsed time.'),
        ),
        migrations.AddField(
            model_name='tag',
            name='meaning',
            field=models.TextField(default='BAD', help_text="A discussion of the tag's semantics. What does it mean? What does it NOT mean?", max_length=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tag',
            name='name',
            field=models.CharField(default='BAD', help_text='A short name for the tag.', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='task',
            name='deadline',
            field=models.DateField(null=True, help_text='If appropriate, specify a deadline by which the task must be completed.'),
        ),
        migrations.AddField(
            model_name='task',
            name='depends_on',
            field=models.ManyToManyField(help_text='If appropriate, specify what tasks must be completed before this one can start.', to='tasks.Task', related_name='depends_on_rel_+'),
        ),
        migrations.AddField(
            model_name='task',
            name='work_estimate',
            field=models.IntegerField(default=0, help_text='Provide an estimate of how much work this tasks requires, in minutes. This is work time, not elapsed time.'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='reviewer',
            field=models.ForeignKey(help_text='A reviewer that will be copied to instances of the recurring task.', null=True, to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='recurringtasktemplate',
            name='short_desc',
            field=models.CharField(help_text='A description that will be copied to instances of the recurring task.', max_length=40),
        ),
        migrations.AlterField(
            model_name='task',
            name='reviewer',
            field=models.ForeignKey(help_text='If required, a member who will review the completed work and either accept or reject it.', null=True, related_name='tasks_to_review', to='tasks.Member'),
        ),
        migrations.AlterField(
            model_name='task',
            name='short_desc',
            field=models.CharField(help_text="A very short description of the task which will be used as it's name. Don't try to provide detailed instructions here - attach a TaskNote instead.", max_length=40),
        ),
        migrations.DeleteModel(
            name='DayInNthWeek',
        ),
        migrations.AddField(
            model_name='tasknote',
            name='task',
            field=models.ForeignKey(to='tasks.Task'),
        ),
    ]
