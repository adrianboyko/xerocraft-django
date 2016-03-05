# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0011_sale_protected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='payer_acct',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL, blank=True, on_delete=django.db.models.deletion.SET_NULL, help_text="It's preferable, but not necessary, to refer to the customer's account.", null=True),
        ),
    ]
