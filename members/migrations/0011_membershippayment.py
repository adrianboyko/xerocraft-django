# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_auto_20160105_1120'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('membership_type', models.CharField(help_text='The type of membership.', max_length=1, choices=[('R', 'Regular'), ('W', 'Work-Trade')])),
                ('payment_method', models.CharField(help_text='The payment method used.', max_length=1, choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2 Checkout'), ('W', 'WePay'), ('P', 'PayPal')])),
                ('paid_by_member', models.DecimalField(help_text='The full amount paid by the member, including payment processing fee IF THEY PAID IT.', max_digits=6, decimal_places=2)),
                ('processing_fee', models.DecimalField(help_text="Payment processor's fee, regardless of whether it was paid by the member or Xerocraft.", max_digits=6, decimal_places=2)),
                ('family_count', models.IntegerField(help_text='The number of ADDITIONAL family members included in this membership. Usually zero.', default=0)),
                ('payment_date', models.DateField(help_text='The date on which the payment was made.', null=True, blank=True)),
                ('start_date', models.DateField(help_text='The frist day on which the membership is valid.')),
                ('end_date', models.DateField(help_text='The last day on which the membership is valid.')),
                ('note', models.TextField(help_text='For staff. Any notes regarding this payment.', max_length=2048)),
                ('paying_member', models.ForeignKey(help_text='The member tagged.', on_delete=django.db.models.deletion.PROTECT, to='members.Member', related_name='payments')),
            ],
        ),
    ]
