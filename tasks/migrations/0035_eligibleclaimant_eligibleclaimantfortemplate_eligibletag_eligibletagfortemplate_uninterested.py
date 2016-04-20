# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0034_worknote'),
    ]

    operations = [
        migrations.CreateModel(
            name='EligibleClaimant',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tasks.task_eligible_claimants',),
        ),
        migrations.CreateModel(
            name='EligibleClaimantForTemplate',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tasks.recurringtasktemplate_eligible_claimants',),
        ),
        migrations.CreateModel(
            name='EligibleTag',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tasks.task_eligible_tags',),
        ),
        migrations.CreateModel(
            name='EligibleTagForTemplate',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tasks.recurringtasktemplate_eligible_tags',),
        ),
        migrations.CreateModel(
            name='Uninterested',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('tasks.recurringtasktemplate_uninterested',),
        ),
    ]
