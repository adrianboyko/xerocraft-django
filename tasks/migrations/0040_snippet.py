# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0039_auto_20160828_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='Snippet',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=40, help_text='The name of the snippet.')),
                ('description', models.CharField(max_length=128, help_text='Short description of what the snippet is about.')),
                ('text', models.TextField(max_length=2048, help_text='The full text content of the snippet.')),
            ],
        ),
    ]
