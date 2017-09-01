# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-08-31 22:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_visitevent_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoverymethod',
            name='visible',
            field=models.BooleanField(default=True, help_text='If people have already chosen them, HIDE method instead of deleting it.'),
        ),
        migrations.AddField(
            model_name='member',
            name='birth_date',
            field=models.DateField(blank=True, help_text='If provided, allows system to adjust when a member reaches the age of majority.', null=True),
        ),
        migrations.AddField(
            model_name='member',
            name='discovery',
            field=models.ManyToManyField(help_text='How this member learned about the organization.', to='members.DiscoveryMethod'),
        ),
        migrations.AddField(
            model_name='member',
            name='is_adult',
            field=models.NullBooleanField(default=None, help_text='Member can specify that they are an adult without providing birth date.'),
        ),
    ]