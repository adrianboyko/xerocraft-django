# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0006_auto_20160221_2349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationnote',
            name='donation',
            field=models.ForeignKey(to='books.Donation'),
        ),
        migrations.AlterField(
            model_name='monetarydonation',
            name='donation',
            field=models.ForeignKey(blank=True, help_text='The donation that includes this line item.', null=True, to='books.Donation'),
        ),
        migrations.AlterField(
            model_name='physicaldonation',
            name='donation',
            field=models.ForeignKey(blank=True, help_text='The donation that includes this line item.', null=True, to='books.Donation'),
        ),
    ]
