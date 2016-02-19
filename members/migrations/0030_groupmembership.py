# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_auto_20160218_1202'),
        ('members', '0029_auto_20160218_1143'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMembership',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('start_date', models.DateField(help_text='The frist day on which the membership is valid.')),
                ('end_date', models.DateField(help_text='The last day on which the membership is valid.')),
                ('max_members', models.IntegerField(null=True, default=None, blank=True, help_text='The maximum number of members to which this group membership can be applied. Blank if no limit.')),
                ('group_tag', models.ForeignKey(to='members.Tag', help_text='The group to which this membership applies, defined by a tag.', on_delete=django.db.models.deletion.PROTECT)),
                ('purchase', models.ForeignKey(to='books.Sale', help_text='The sale that includes this line item.', null=True, blank=True, on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
