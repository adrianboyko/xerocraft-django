# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0032_auto_20160219_1202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membershipgiftcardreference',
            name='card',
            field=models.OneToOneField(help_text='The membership gift card being sold.', to='members.MembershipGiftCard', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='membership_type',
            field=models.CharField(help_text='The type of membership.', default='R', max_length=1, choices=[('R', 'Regular'), ('W', 'Work-Trade'), ('S', 'Scholarship'), ('C', 'Complimentary'), ('G', 'Group')]),
        ),
    ]
