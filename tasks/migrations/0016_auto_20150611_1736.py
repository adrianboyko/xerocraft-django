# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_auto_20150611_1610'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='member',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='member',
            name='user_id',
        ),
        migrations.AlterField(
            model_name='member',
            name='auth_user',
            field=models.OneToOneField(default=None, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
