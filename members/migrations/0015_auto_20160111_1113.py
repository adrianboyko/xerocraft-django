# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0014_auto_20160111_1108'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaidMembership',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('membership_type', models.CharField(default='R', help_text='The type of membership.', max_length=1, choices=[('R', 'Regular'), ('W', 'Work-Trade'), ('S', 'Scholarship')])),
                ('family_count', models.IntegerField(default=0, help_text='The number of ADDITIONAL family members included in this membership. Usually zero.')),
                ('start_date', models.DateField(help_text='The frist day on which the membership is valid.')),
                ('end_date', models.DateField(help_text='The last day on which the membership is valid.')),
                ('payer_name', models.CharField(help_text='No need to provide this if member was linked above.', max_length=40, blank=True)),
                ('payer_email', models.EmailField(help_text='No need to provide this if member was linked above.', max_length=40, blank=True)),
                ('payment_method', models.CharField(default='$', help_text='The payment method used.', max_length=1, choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')])),
                ('paid_by_member', models.DecimalField(decimal_places=2, help_text='The full amount paid by the member, including payment processing fee IF THEY PAID IT.', max_digits=6)),
                ('processing_fee', models.DecimalField(decimal_places=2, help_text="Payment processor's fee, regardless of whether it was paid by the member or Xerocraft.", max_digits=6)),
                ('payment_date', models.DateField(help_text='The date on which the payment was made. Can be blank if unknown.', blank=True, null=True)),
                ('member', models.ForeignKey(to='members.Member', default=None, help_text='The member who made the payment.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='terms', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='membershipterm',
            name='member',
        ),
        migrations.DeleteModel(
            name='MembershipTerm',
        ),
    ]
