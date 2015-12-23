# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_auto_20151012_1240'),
        ('tasks', '0033_auto_20151213_1305'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('when_written', models.DateTimeField(help_text='The date and time when the note was written.', auto_now_add=True)),
                ('content', models.TextField(help_text='Anything you want to say about the work done.', max_length=2048)),
                ('author', models.ForeignKey(to='members.Member', on_delete=django.db.models.deletion.SET_NULL, help_text='The member who wrote this note.', null=True, related_name='work_notes_authored', blank=True)),
                ('work', models.ForeignKey(related_name='notes', to='tasks.Work')),
            ],
        ),
    ]
