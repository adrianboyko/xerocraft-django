# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0035_eligibleclaimant_eligibleclaimantfortemplate_eligibletag_eligibletagfortemplate_uninterested'),
    ]

    operations = [
        migrations.AddField(
            model_name='nag',
            name='claims',
            field=models.ManyToManyField(to='tasks.Claim', help_text='The claim that the member was asked to verify.'),
        ),
    ]
