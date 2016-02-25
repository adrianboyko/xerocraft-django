# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0009_auto_20160225_1442'),
        ('members', '0037_discoverymethod'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipReimbursement',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('members.membership',),
        ),
        migrations.AddField(
            model_name='membership',
            name='claim',
            field=models.ForeignKey(blank=True, null=True, to='books.ExpenseClaim', help_text='The claim on which this membership appears as a reimbursement.'),
        ),
        migrations.AlterField(
            model_name='groupmembership',
            name='sale',
            field=models.ForeignKey(default=None, to='books.Sale', help_text='The sale on which this group membership appears as a line item, if any.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='membership',
            name='sale',
            field=models.ForeignKey(blank=True, null=True, to='books.Sale', help_text="The sale that includes this line item, if any. E.g. comp memberships don't have a corresponding sale."),
        ),
        migrations.AlterField(
            model_name='membershipgiftcardreference',
            name='sale',
            field=models.ForeignKey(blank=True, null=True, to='books.Sale', help_text='The sale that includes the card as a line item.'),
        ),
    ]
