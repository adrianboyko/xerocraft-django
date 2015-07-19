# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('membership_card_md5', models.CharField(blank=True, null=True, max_length=32, help_text='MD5 checksum of the random urlsafe base64 string on the membership card.')),
                ('membership_card_when', models.DateTimeField(blank=True, null=True, help_text='Date/time on which the membership card was created.')),
                ('auth_user', models.OneToOneField(related_name='member', to=settings.AUTH_USER_MODEL, help_text='This must point to the corresponding auth.User object.')),
            ],
        ),
        migrations.CreateModel(
            name='MemberNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('content', models.TextField(help_text='For staff. Anything you want to say about the member.', max_length=2048)),
                ('author', models.ForeignKey(related_name='member_notes_authored', null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Member', help_text='The member who wrote this note.', blank=True)),
                ('task', models.ForeignKey(to='members.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='A short name for the tag.', max_length=40, unique=True)),
                ('meaning', models.TextField(help_text="A discussion of the tag's semantics. What does it mean? What does it NOT mean?", max_length=500)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='members', to='members.Tag'),
        ),
    ]
