# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import members.models
import datetime
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0042_auto_20160303_1717'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membership',
            name='claim',
        ),
        migrations.AddField(
            model_name='membership',
            name='sale_price',
            field=models.DecimalField(decimal_places=2, max_digits=6, help_text='The price at which this item sold.', default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='membershipgiftcardreference',
            name='ctrlid',
            field=models.CharField(help_text="Payment processor's id if this was part of an online purchase.", max_length=40, unique=True, default=members.models.next_giftcardref_ctrlid),
        ),
        migrations.AddField(
            model_name='membershipgiftcardreference',
            name='protected',
            field=models.BooleanField(help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.', default=False),
        ),
        migrations.AddField(
            model_name='membershipgiftcardreference',
            name='sale_price',
            field=models.DecimalField(decimal_places=2, max_digits=6, help_text='The price at which this item sold.', default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupmembership',
            name='start_date',
            field=models.DateField(help_text='The first day on which the membership is valid.'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='end_date',
            field=models.DateField(help_text='The last day on which the membership is valid.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='membership',
            name='sale',
            field=models.ForeignKey(blank=True, help_text="The sale that includes this line item, if any. E.g. comp memberships don't have a corresponding sale.", default=None, null=True, to='books.Sale'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='start_date',
            field=models.DateField(help_text='The first day on which the membership is valid.', default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='membershipgiftcardreference',
            name='card',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, blank=True, help_text='The membership gift card being sold.', null=True, to='members.MembershipGiftCard'),
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='start_date',
            field=models.DateField(help_text='The first day on which the membership is valid.'),
        ),
    ]
