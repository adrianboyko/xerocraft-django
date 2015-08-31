# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_auto_20150830_2007'),
        ('tasks', '0005_auto_20150822_2358'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('when', models.DateTimeField(help_text='The date and time when member was asked to work the task.', auto_now_add=True)),
                ('auth_token_md5', models.CharField(help_text="MD5 checksum of the random urlsafe base64 string used in the nagging email's URLs.", max_length=32)),
            ],
        ),
        migrations.RenameField(
            model_name='recurringtasktemplate',
            old_name='nag',
            new_name='should_nag',
        ),
        migrations.RenameField(
            model_name='task',
            old_name='nag',
            new_name='should_nag',
        ),
        migrations.AlterField(
            model_name='claim',
            name='date',
            field=models.DateField(help_text='The date on which the member claimed the task.'),
        ),
        migrations.AlterField(
            model_name='claim',
            name='member',
            field=models.ForeignKey(help_text='The member claiming the task.', to='members.Member'),
        ),
        migrations.AlterField(
            model_name='claim',
            name='status',
            field=models.CharField(choices=[('C', 'Current'), ('X', 'Expired'), ('Q', 'Queued')], help_text='The status of this claim.', max_length=1),
        ),
        migrations.AlterField(
            model_name='claim',
            name='task',
            field=models.ForeignKey(help_text='The task against which the claim to work is made.', to='tasks.Task'),
        ),
        migrations.AddField(
            model_name='nag',
            name='tasks',
            field=models.ManyToManyField(to='tasks.Task', help_text='The task that the member was asked to work.'),
        ),
        migrations.AddField(
            model_name='nag',
            name='who',
            field=models.ForeignKey(help_text='The member who was nagged.', null=True, to='members.Member', on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
