# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0034_auto_20160221_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmembership',
            name='sale',
            field=models.ForeignKey(help_text='The sale that includes this line item.', blank=True, to='books.Sale', null=True),
        ),
        migrations.AlterField(
            model_name='membership',
            name='sale',
            field=models.ForeignKey(help_text='The sale that includes this line item.', blank=True, to='books.Sale', null=True),
        ),
        migrations.AlterField(
            model_name='membershipgiftcardreference',
            name='sale',
            field=models.ForeignKey(help_text='The sale that includes this line item.', blank=True, to='books.Sale', null=True),
        ),
    ]
