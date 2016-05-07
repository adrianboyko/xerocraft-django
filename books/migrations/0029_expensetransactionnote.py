# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0028_expenselineitem_receipt_num'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseTransactionNote',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('content', models.TextField(max_length=2048, help_text='Anything you want to say about the item on which this note appears.')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, help_text='The user who wrote this note.', null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('exp', models.ForeignKey(to='books.ExpenseTransaction', help_text='The expense transaction to which the note pertains.')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
