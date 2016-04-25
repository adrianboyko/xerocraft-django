# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0046_auto_20160420_1107'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pushover',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('key', models.CharField(max_length=30, help_text="The member's User Key on Pushover.com")),
                ('who', models.ForeignKey(to='members.Member', help_text='The member to whom this tagging info applies.')),
            ],
        ),
    ]
