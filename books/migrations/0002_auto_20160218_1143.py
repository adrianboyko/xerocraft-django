# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donation',
            name='payer_email',
        ),
        migrations.RemoveField(
            model_name='donation',
            name='payer_name',
        ),
        migrations.AddField(
            model_name='donation',
            name='donators_email',
            field=models.EmailField(blank=True, help_text='Email address of person who made the donation.', max_length=40),
        ),
        migrations.AddField(
            model_name='donation',
            name='donators_name',
            field=models.CharField(blank=True, help_text='Name of person who made the donation.', max_length=40),
        ),
        migrations.AlterField(
            model_name='monetarydonation',
            name='donation',
            field=models.ForeignKey(blank=True, help_text='The donation that includes this line item.', to='books.Donation', null=True, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='physicaldonation',
            name='donation',
            field=models.ForeignKey(blank=True, help_text='The donation that includes this line item.', to='books.Donation', null=True, on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
