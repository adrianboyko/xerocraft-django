# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-15 04:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_auto_20170405_1551'),
        ('inventory', '0002_auto_20170512_1440'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsumableToStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_desc', models.CharField(help_text='The items name or a short description.', max_length=40)),
                ('obtain_from', models.CharField(help_text='A suggested retailer to obtain the item from.', max_length=40)),
                ('min_level', models.IntegerField(help_text='Restock when inventory reaches this low level.')),
                ('min_level_unit', models.CharField(help_text='Unit of restock.', max_length=10)),
                ('restock_required', models.BooleanField(default=False, help_text='Set this if you notice that a restock is required.')),
                ('for_shop', models.ForeignKey(blank=True, help_text='The shop that requested that this item be stocked.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.Shop')),
                ('stocker', models.ForeignKey(blank=True, help_text='The Quartermaster if blank, else their delegate.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Member')),
            ],
            options={
                'verbose_name_plural': 'Consumables to stock',
            },
        ),
        migrations.RemoveField(
            model_name='tool',
            name='name',
        ),
        migrations.AlterField(
            model_name='location',
            name='short_desc',
            field=models.CharField(help_text='A short description/name for the location.', max_length=40),
        ),
        migrations.AlterField(
            model_name='parkingpermit',
            name='billing_period',
            field=models.CharField(choices=[('/', 'N/A'), ('W', 'Weeks'), ('M', 'Months'), ('Q', 'Quarters'), ('Y', 'Years')], default='/', help_text='The price per period will be billed at this frequency.', max_length=1),
        ),
        migrations.AlterField(
            model_name='parkingpermit',
            name='short_desc',
            field=models.CharField(help_text='The items name or a short description.', max_length=40),
        ),
        migrations.AlterField(
            model_name='tool',
            name='short_desc',
            field=models.CharField(help_text='The items name or a short description.', max_length=40),
        ),
    ]