# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('membership_card_md5', models.CharField(max_length=32, null=True, help_text='MD5 checksum of the random urlsafe base64 string on the membership card.', blank=True)),
                ('membership_card_when', models.DateTimeField(blank=True, null=True, help_text='Date/time on which the membership card was created.')),
                ('auth_user', models.OneToOneField(related_name='member', to=settings.AUTH_USER_MODEL, help_text='This must point to the corresponding auth.User object.')),
            ],
        ),
        migrations.CreateModel(
            name='MemberNote',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('content', models.TextField(max_length=2048, help_text='For staff. Anything you want to say about the member.')),
                ('author', models.ForeignKey(related_name='member_notes_authored', null=True, to='members.Member', on_delete=django.db.models.deletion.SET_NULL, help_text='The member who wrote this note.', blank=True)),
                ('task', models.ForeignKey(to='members.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True, help_text='A short name for the tag.')),
                ('meaning', models.TextField(max_length=500, help_text="A discussion of the tag's semantics. What does it mean? What does it NOT mean?")),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Tagging',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('can_tag', models.BooleanField(help_text='If True, the tagged member can be a authorizing member for this tag.', default=False)),
                ('authorizing_member', models.ForeignKey(related_name='authorized_taggings', to='members.Member', help_text='The member that authorized that the member be tagged.')),
                ('tag', models.ForeignKey(to='members.Tag', help_text='The tag assigned to the member.')),
                ('tagged_member', models.ForeignKey(related_name='taggings', to='members.Member', help_text='The member tagged.')),
            ],
        ),
        migrations.AddField(
            model_name='member',
            name='tags',
            field=models.ManyToManyField(related_name='members', blank=True, to='members.Tag', through='members.Tagging'),
        ),
    ]
