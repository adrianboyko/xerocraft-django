# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_auto_20160221_2216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salenote',
            name='sale',
            field=models.ForeignKey(to='books.Sale'),
        ),
    ]
