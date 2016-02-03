# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0021_auto_20160127_2347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paidmembership',
            name='membership_type',
            field=models.CharField(max_length=1, default='R', choices=[('R', 'Regular'), ('W', 'Work-Trade'), ('S', 'Scholarship'), ('C', 'Complimentary')], help_text='The type of membership.'),
        ),
    ]
