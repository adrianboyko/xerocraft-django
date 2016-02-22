# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0007_auto_20160221_2352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationnote',
            name='donation',
            field=models.ForeignKey(help_text='The donation to which this note applies.', to='books.Donation'),
        ),
        migrations.AlterField(
            model_name='salenote',
            name='sale',
            field=models.ForeignKey(help_text='The sale to which the note pertains.', to='books.Sale'),
        ),
    ]
