# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0038_accountgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=40, help_text='Name of person/organization.')),
                ('email', models.EmailField(max_length=40, help_text='Email address of person/organization.', blank=True)),
            ],
            options={
                'verbose_name': 'Non-Member Entity',
                'verbose_name_plural': 'Non-Member Entities',
            },
        ),
        migrations.CreateModel(
            name='EntityNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.')),
                ('author', models.ForeignKey(help_text='The user who wrote this note.', null=True, to=settings.AUTH_USER_MODEL, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('entity', models.ForeignKey(help_text='The entity to which the note pertains.', to='books.Entity')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('date_invoiced', models.DateField(help_text='The date on which the invoice was created and presumably mailed.', default=datetime.date.today)),
                ('amount', models.DecimalField(decimal_places=2, help_text='The dollar amount of the payment.', max_digits=6)),
                ('description', models.TextField(max_length=4096, help_text='Description of goods and/or services delivered.')),
                ('account', models.ForeignKey(to='books.Account', help_text='The revenue account associated with this invoice.', on_delete=django.db.models.deletion.PROTECT)),
                ('entity_invoiced', models.ForeignKey(help_text='If some outside person/org is being invoiced, specify them here.', null=True, to='books.Entity', blank=True, default=None, on_delete=django.db.models.deletion.SET_NULL)),
                ('user_invoiced', models.ForeignKey(help_text='If a user is being invoiced, specify them here.', null=True, to=settings.AUTH_USER_MODEL, blank=True, default=None, on_delete=django.db.models.deletion.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.')),
                ('author', models.ForeignKey(help_text='The user who wrote this note.', null=True, to=settings.AUTH_USER_MODEL, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('invoice', models.ForeignKey(help_text='The invoice to which the note pertains.', to='books.Invoice')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvoiceReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('portion', models.DecimalField(blank=True, max_digits=6, null=True, decimal_places=2, help_text="Leave blank unless you're only paying a portion of the invoice.", default=None)),
                ('invoice', models.ForeignKey(help_text='The invoice that is paid by the income transaction.', to='books.Invoice')),
                ('sale', models.ForeignKey(help_text='The income transaction that pays the invoice.', to='books.Sale')),
            ],
        ),
        migrations.AddField(
            model_name='expensetransaction',
            name='recipient_entity',
            field=models.ForeignKey(help_text='If some outside person/org is being invoiced, specify them here.', null=True, to='books.Entity', blank=True, default=None, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
