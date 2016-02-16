# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0026_auto_20160215_1533'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donationlineitem',
            name='description',
        ),
        migrations.RemoveField(
            model_name='donationlineitem',
            name='value',
        ),
        migrations.AddField(
            model_name='donationlineitem',
            name='amount',
            field=models.DecimalField(help_text='The amount donated.', decimal_places=2, max_digits=6, default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='donationlineitem',
            name='purchase',
            field=models.ForeignKey(help_text='The payment that includes this donation as a line item.', null=True, to='members.Purchase', blank=True, on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
