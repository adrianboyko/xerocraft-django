# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_auto_20160109_1803'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('paying_name', models.CharField(blank=True, max_length=40, help_text='No need to provide this if member was linked above.')),
                ('payment_method', models.CharField(default='$', choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2 Checkout'), ('W', 'WePay'), ('P', 'PayPal')], max_length=1, help_text='The payment method used.')),
                ('paid_by_member', models.DecimalField(max_digits=6, decimal_places=2, help_text='The full amount paid by the member, including payment processing fee IF THEY PAID IT.')),
                ('processing_fee', models.DecimalField(max_digits=6, decimal_places=2, help_text="Payment processor's fee, regardless of whether it was paid by the member or Xerocraft.")),
                ('payment_date', models.DateField(blank=True, null=True, help_text='The date on which the payment was made. Can be blank if unknown.')),
                ('paying_member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', null=True, blank=True, to='members.Member', help_text='The member who made the payment.')),
            ],
        ),
    ]
