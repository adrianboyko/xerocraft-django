# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import books.models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0015_auto_20160304_2237'),
    ]

    operations = [
        migrations.CreateModel(
            name='OtherItem',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('sale_price', models.DecimalField(decimal_places=2, help_text='The UNIT price at which this/these item(s) sold.', max_digits=6)),
                ('qty_sold', models.IntegerField(default=1, help_text='The quantity of the item sold.')),
                ('ctrlid', models.CharField(max_length=40, default=books.models.next_monetarydonation_ctrlid, unique=True, help_text="Payment processor's id for this donation, if any.")),
                ('protected', models.BooleanField(default=False, help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually entered data.')),
                ('sale', models.ForeignKey(to='books.Sale', help_text='The sale for which this is a line item.')),
            ],
        ),
        migrations.CreateModel(
            name='OtherItemType',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=40, unique=True, help_text='A short name for the item.')),
                ('description', models.TextField(max_length=1024, help_text='A description of the item.')),
            ],
        ),
        migrations.AddField(
            model_name='otheritem',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=None, help_text='The type of item sold.', to='books.OtherItemType'),
        ),
    ]
