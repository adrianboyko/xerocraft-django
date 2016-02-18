# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import books.models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('donation_date', models.DateField(default=django.utils.timezone.now, help_text='The date on which the donation was made. Best guess if exact date not known.')),
                ('payer_name', models.CharField(max_length=40, blank=True, help_text='Name of person who made the payment.')),
                ('payer_email', models.EmailField(max_length=40, blank=True, help_text='Email address of person who made the payment.')),
            ],
        ),
        migrations.CreateModel(
            name='DonationNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the sale.')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, help_text='The member who wrote this note.', null=True)),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='books.Donation')),
            ],
        ),
        migrations.CreateModel(
            name='MonetaryDonation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6, help_text='The amount donated.')),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='books.Donation', help_text='The sale that includes this line item.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PhysicalDonation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('value', models.DecimalField(decimal_places=2, max_digits=6, help_text='The value of the item donated.')),
                ('description', models.TextField(max_length=1024, help_text='A description of the item donated.')),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='books.Donation', help_text='The sale that includes this line item.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('sale_date', models.DateField(default=django.utils.timezone.now, help_text='The date on which the sale was made. Best guess if exact date not known.')),
                ('payer_name', models.CharField(max_length=40, blank=True, help_text='Name of person who made the payment.')),
                ('payer_email', models.EmailField(max_length=40, blank=True, help_text='Email address of person who made the payment.')),
                ('payment_method', models.CharField(default='$', max_length=1, help_text='The payment method used.', choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')])),
                ('total_paid_by_customer', models.DecimalField(decimal_places=2, max_digits=6, help_text='The full amount paid by the person, including payment processing fee IF CUSTOMER PAID IT.')),
                ('processing_fee', models.DecimalField(decimal_places=2, default=0, max_digits=6, help_text="Payment processor's fee, REGARDLESS OF WHO PAID FOR IT. Zero for cash/check.")),
                ('ctrlid', models.CharField(default=books.models.next_sale_ctrlid, help_text="Payment processor's id for this payment.", max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='SaleNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the sale.')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, help_text='The member who wrote this note.', null=True)),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='books.Sale')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='sale',
            unique_together=set([('payment_method', 'ctrlid')]),
        ),
    ]
