# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_auto_20160218_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='method_detail',
            field=models.CharField(help_text='Optional detail specific to the payment method. Check# for check payments.', max_length=40, blank=True),
        ),
    ]
