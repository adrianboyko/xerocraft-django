# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0037_unavailabledates'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EligibleClaimant',
        ),
        migrations.DeleteModel(
            name='EligibleClaimantForTemplate',
        ),
        migrations.DeleteModel(
            name='EligibleTag',
        ),
        migrations.DeleteModel(
            name='EligibleTagForTemplate',
        ),
        migrations.DeleteModel(
            name='Uninterested',
        ),
    ]
