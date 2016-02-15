# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import members.models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0024_auto_20160212_1303'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonationLineItem',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('value', models.DecimalField(max_digits=6, help_text='The amount for a monetary donation or the assessed value for physical item(s) donated.', decimal_places=2)),
                ('description', models.TextField(max_length=2048, help_text='Description, if physical items are being donated. Blank for monetary donation.')),
            ],
        ),
        migrations.CreateModel(
            name='MembershipGiftCard',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('redemption_code', models.CharField(unique=True, max_length=20, help_text='A random string printed on the card, used during card redemption / membership activation.')),
                ('date_created', models.DateField(help_text='The date on which the gift card was created.', default=django.utils.timezone.now)),
                ('price', models.DecimalField(max_digits=6, help_text='The price to buy this gift card.', decimal_places=2)),
                ('month_duration', models.IntegerField(help_text='The number of months of membership this gift card grants when redeemed.')),
            ],
        ),
        migrations.CreateModel(
            name='MembershipGiftCardLineItem',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('card', models.OneToOneField(to='members.MembershipGiftCard', help_text='The membership gift card that was purchased.', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='PaidMembershipNudge',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('when', models.DateField(help_text='Date on which the member was reminded.', default=django.utils.timezone.now)),
                ('member', models.ForeignKey(help_text='The member we reminded.', to='members.Member')),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('payment_date', models.DateField(help_text='The date on which the payment was made. Best guess if exact date not known.', default=django.utils.timezone.now)),
                ('payer_name', models.CharField(max_length=40, blank=True, help_text='Name of person who made the payment.')),
                ('payer_email', models.EmailField(max_length=40, blank=True, help_text='Email address of person who made the payment.')),
                ('payment_method', models.CharField(choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')], max_length=1, help_text='The payment method used.', default='$')),
                ('total_paid_by_customer', models.DecimalField(max_digits=6, help_text='The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.', decimal_places=2)),
                ('processing_fee', models.DecimalField(max_digits=6, help_text="Payment processor's fee, REGARDLESS OF WHO PAID FOR IT. Zero for cash/check.", default=0, decimal_places=2)),
                ('ctrlid', models.CharField(max_length=40, help_text="Payment processor's id for this payment.", default=members.models.next_payment_ctrlid)),
            ],
        ),
        migrations.RemoveField(
            model_name='paymentreminder',
            name='member',
        ),
        migrations.DeleteModel(
            name='PaymentReminder',
        ),
        migrations.AddField(
            model_name='membershipgiftcardlineitem',
            name='purchase',
            field=models.ForeignKey(to='members.Purchase', help_text='The payment that includes this gift card as a line item.', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='donationlineitem',
            name='purchase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='members.Purchase', help_text='If donation is monetary, this is the payment that includes it as a line item. Else blank.', blank=True, null=True),
        ),
    ]
