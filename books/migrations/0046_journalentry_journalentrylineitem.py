# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-01-04 04:05
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0045_auto_20161028_1139'),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('frozen', models.BooleanField(default=False, help_text="If frozen, this entry (and its lines) won't be deleted/regenerated.")),
                ('source_url', models.URLField(help_text='URL to retrieve the item that gave rise to this journal entry.')),
                ('when', models.DateField(help_text='The date of the transaction.')),
            ],
        ),
        migrations.CreateModel(
            name='JournalEntryLineItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('>', 'Increase'), ('<', 'Decrease')], help_text='Is the account balance increased or decreased?', max_length=1)),
                ('amount', models.DecimalField(decimal_places=2, help_text='The amount of the increase or decrease (always positive)', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('account', models.ForeignKey(help_text='.', on_delete=django.db.models.deletion.PROTECT, to='books.Account')),
                ('journal_entry', models.ForeignKey(help_text='.', on_delete=django.db.models.deletion.CASCADE, to='books.JournalEntry')),
            ],
        ),
    ]
