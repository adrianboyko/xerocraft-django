# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0051_auto_20160604_2137'),
        ('inventory', '0004_auto_20151224_2226'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='The name of the shop.', max_length=40)),
                ('info_link', models.URLField(null=True, blank=True, help_text='A link to some web-based info about the shop, e.g. a Wiki page.')),
                ('backup_manager', models.ForeignKey(null=True, related_name='shops_backed', to='members.Member', help_text='The member that can carry out manager duties when the manager is not available.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
                ('manager', models.ForeignKey(null=True, related_name='shops_managed', to='members.Member', help_text='The member that manages the shop.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text="The resource's name or a short description.", max_length=40)),
                ('location', models.ForeignKey(null=True, to='inventory.Location', help_text='The location of the resource.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
                ('shop', models.ForeignKey(null=True, to='inventory.Shop', help_text='The shop that owns or stocks the resource.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ToolIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_desc', models.CharField(help_text='A short description of the issue. In depth description can go in a note.', max_length=40)),
                ('status', models.CharField(choices=[('N', 'New Issue'), ('V', 'Validated'), ('C', 'Closed')], max_length=1)),
                ('reporter', models.ForeignKey(null=True, to='members.Member', help_text='The member that reported the issue.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
                ('tool', models.ForeignKey(help_text='The member that reported the issue.', to='inventory.Tool')),
            ],
        ),
        migrations.CreateModel(
            name='ToolIssueNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('when_written', models.DateTimeField(help_text='The date and time when the note was written.', auto_now_add=True)),
                ('content', models.TextField(help_text='Anything you want to say about the tool issue.', max_length=2048)),
                ('author', models.ForeignKey(null=True, to='members.Member', help_text='The member who wrote this note.', on_delete=django.db.models.deletion.SET_NULL, blank=True)),
                ('toolIssue', models.ForeignKey(help_text='Any kind of note about the tool issue.', to='inventory.ToolIssue')),
            ],
        ),
    ]
