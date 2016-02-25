# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0008_auto_20160222_1224'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=40, blank=True, help_text='Name of the account.')),
                ('category', models.CharField(choices=[('A', 'Asset'), ('L', 'Liability'), ('Q', 'Equity'), ('R', 'Revenue'), ('X', 'Expense')], max_length=1, help_text='The category of the account.')),
                ('type', models.CharField(choices=[('C', 'Credit'), ('D', 'Debit')], max_length=1, help_text='The type of the account.')),
                ('description', models.TextField(max_length=1024, help_text="A discussion of the account's purpose. What is it for? What is it NOT for?")),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The user who manages this account.')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseClaim',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('claim_date', models.DateField(default=django.utils.timezone.now, help_text='The date on which the claim was filed. Best guess if exact date not known.')),
                ('claimant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The member who wrote this note.')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseClaimLineItem',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=80, blank=True, help_text='A brief description of this line item.')),
                ('expense_date', models.DateField(help_text='The date on which the expense was incurred, from the receipt.')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6, help_text='The dollar amount for this line item, from the receipt.')),
                ('account', models.ForeignKey(to='books.Account', help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.")),
                ('claim', models.ForeignKey(to='books.ExpenseClaim', help_text='The claim on which this line item appears.')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseClaimNote',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The user who wrote this note.')),
                ('claim', models.ForeignKey(to='books.ExpenseClaim', help_text='The claim to which the note pertains.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MonetaryReimbursement',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6, help_text='The dollar amount reimbursed.')),
                ('payment_method', models.CharField(choices=[('$', 'Cash'), ('C', 'Check')], max_length=1, default='$', help_text='The payment method used.')),
                ('method_detail', models.CharField(max_length=40, blank=True, help_text='Optional detail specific to the payment method. Check# for check payments.')),
                ('claim', models.ForeignKey(to='books.ExpenseClaim', help_text='The claim on which this reimbursement appears.')),
            ],
        ),
        migrations.CreateModel(
            name='MonetaryDonationReimbursement',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('books.monetarydonation',),
        ),
        migrations.AddField(
            model_name='donation',
            name='donator_acct',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text="It's preferable, but not necessary, to refer to the donator's account."),
        ),
        migrations.AddField(
            model_name='monetarydonation',
            name='sale',
            field=models.ForeignKey(blank=True, null=True, to='books.Sale', help_text='The sale that includes this line item.'),
        ),
        migrations.AddField(
            model_name='sale',
            name='payer_acct',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text="It's preferable, but not necessary, to refer to the customer's account."),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donator_name',
            field=models.CharField(max_length=40, blank=True, help_text='Name of person who made the donation. Not necessary if account is linked.'),
        ),
        migrations.AlterField(
            model_name='donationnote',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The user who wrote this note.'),
        ),
        migrations.AlterField(
            model_name='donationnote',
            name='content',
            field=models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.'),
        ),
        migrations.AlterField(
            model_name='physicaldonation',
            name='donation',
            field=models.ForeignKey(default=None, to='books.Donation', help_text='The donation that includes this line item.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sale',
            name='payer_name',
            field=models.CharField(max_length=40, blank=True, help_text='Name of person who made the payment. Not necessary if account was linked.'),
        ),
        migrations.AlterField(
            model_name='salenote',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The user who wrote this note.'),
        ),
        migrations.AlterField(
            model_name='salenote',
            name='content',
            field=models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.'),
        ),
        migrations.AddField(
            model_name='monetarydonation',
            name='claim',
            field=models.ForeignKey(blank=True, null=True, to='books.ExpenseClaim', help_text='The claim on which this reimbursement appears.'),
        ),
    ]
