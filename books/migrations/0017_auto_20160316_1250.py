# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0016_auto_20160314_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='donation_date',
            field=models.DateField(help_text='The date on which the donation was made. Best guess if exact date not known.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='expenseclaim',
            name='claim_date',
            field=models.DateField(help_text='The date on which the claim was filed. Best guess if exact date not known.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='sale',
            name='sale_date',
            field=models.DateField(help_text='The date on which the sale was made. Best guess if exact date not known.', default=datetime.date.today),
        ),
    ]
