# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0029_expensetransactionnote'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='expenselineitem',
            name='approved_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, default=None, help_text='Usually the shop/account manager. Leave blank if not yet approved.', blank=True),
        ),
    ]
