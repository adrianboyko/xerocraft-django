# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0018_auto_20160323_1309'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='expensetransaction',
            name='account',
        ),
        migrations.AddField(
            model_name='expensetransaction',
            name='payment_date',
            field=models.DateField(default=datetime.date.today, help_text='The date on which the expense was paid. Best guess if exact date not known.'),
        ),
        migrations.AddField(
            model_name='expensetransaction',
            name='recipient_acct',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, default=None, help_text='If payment was made to a member, specify them here.', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='expensetransaction',
            name='recipient_email',
            field=models.EmailField(help_text='Email address of person/organization to whom the payment was made.', blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='expensetransaction',
            name='recipient_name',
            field=models.CharField(help_text='Name of person/organization to whom payment was made. Not necessary if member was linked, above.', blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='expensetransaction',
            name='amount',
            field=models.DecimalField(max_digits=6, decimal_places=2, help_text='The dollar amount of the payment.'),
        ),
    ]
