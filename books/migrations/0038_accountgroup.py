# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0037_sale_deposit_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=40, help_text='Name of the group.')),
                ('description', models.TextField(max_length=1024, help_text="The group's purpose, e.g. 'This acct group corresponds to a budget line item.'")),
                ('accounts', models.ManyToManyField(to='books.Account', help_text='The accounts that are part of this group.')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
