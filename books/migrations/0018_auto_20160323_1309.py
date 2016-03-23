# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0017_auto_20160316_1250'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonatedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('value', models.DecimalField(help_text='The value of the item donated.', max_digits=6, decimal_places=2)),
                ('description', models.TextField(help_text='A description of the item donated.', max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseClaimReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('amount', models.DecimalField(help_text='The dollar amount reimbursed.', max_digits=6, decimal_places=2)),
                ('payment_method', models.CharField(help_text='The payment method used.', default='$', max_length=1, choices=[('$', 'Cash'), ('C', 'Check')])),
                ('method_detail', models.CharField(help_text='Optional detail specific to the payment method. Check# for check payments.', blank=True, max_length=40)),
                ('account', models.ForeignKey(help_text="The account against which this line item is claimed, e.g. 'Wood Shop', '3D Printers'.", to='books.Account')),
            ],
        ),
        migrations.RemoveField(
            model_name='monetaryreimbursement',
            name='claim',
        ),
        migrations.RemoveField(
            model_name='physicaldonation',
            name='donation',
        ),
        migrations.AlterModelOptions(
            name='donation',
            options={'verbose_name': 'Physical donation'},
        ),
        migrations.AlterModelOptions(
            name='sale',
            options={'verbose_name': 'Income transaction'},
        ),
        migrations.RemoveField(
            model_name='monetarydonation',
            name='donation',
        ),
        migrations.AddField(
            model_name='expenseclaim',
            name='amount',
            field=models.DecimalField(help_text='The dollar amount for the entire claim.', default=0, max_digits=6, decimal_places=2),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='monetarydonation',
            name='sale',
            field=models.ForeignKey(help_text='The sale that includes this line item.', default=None, to='books.Sale'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='MonetaryReimbursement',
        ),
        migrations.DeleteModel(
            name='PhysicalDonation',
        ),
        migrations.AddField(
            model_name='expenseclaimreference',
            name='claim',
            field=models.ForeignKey(help_text='The claim that is paid by the expense transaction.', to='books.ExpenseClaim'),
        ),
        migrations.AddField(
            model_name='expenseclaimreference',
            name='exp',
            field=models.ForeignKey(help_text='The expense transaction that pays the claim.', to='books.ExpenseTransaction'),
        ),
        migrations.AddField(
            model_name='donateditem',
            name='donation',
            field=models.ForeignKey(help_text='The donation that includes this line item.', to='books.Donation'),
        ),
    ]
