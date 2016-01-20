# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0017_auto_20160116_0116'),
    ]

    operations = [
        migrations.AddField(
            model_name='paidmembership',
            name='payer_notes',
            field=models.CharField(max_length=1024, blank=True, help_text='Any notes provided by the member.'),
        ),
        migrations.AddField(
            model_name='paidmembership',
            name='protect_from_etl',
            field=models.BooleanField(help_text='Prevents further mods to payment by ETL process. Protects manual changes.', default=False),
        ),
    ]
