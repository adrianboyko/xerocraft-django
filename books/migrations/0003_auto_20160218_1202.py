# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_auto_20160218_1143'),
    ]

    operations = [
        migrations.RenameField(
            model_name='donation',
            old_name='donators_email',
            new_name='donator_email',
        ),
        migrations.RenameField(
            model_name='donation',
            old_name='donators_name',
            new_name='donator_name',
        ),
    ]
