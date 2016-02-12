# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0023_auto_20160203_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberLogin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('when', models.DateTimeField(default=django.utils.timezone.now, help_text='Date/time member logged in.')),
                ('ip', models.GenericIPAddressField(help_text='IP address from which member logged in.')),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text='The member who logged in.', to='members.Member')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentReminder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('when', models.DateField(default=django.utils.timezone.now, help_text='Date on which the member was reminded.')),
                ('member', models.ForeignKey(to='members.Member', help_text='The member we reminded.')),
            ],
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='member',
            field=models.ForeignKey(null=True, default=None, on_delete=django.db.models.deletion.PROTECT, related_name='terms', blank=True, help_text='The member to whom this paid membership applies.', to='members.Member'),
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='payer_email',
            field=models.EmailField(blank=True, help_text='Email address of person who made the payment.', max_length=40),
        ),
        migrations.AlterField(
            model_name='paidmembership',
            name='payer_name',
            field=models.CharField(blank=True, help_text='Name of person who made the payment.', max_length=40),
        ),
        migrations.AlterField(
            model_name='paymentaka',
            name='aka',
            field=models.CharField(help_text="The AKA, probably their spouse's name or a simple variation on their own name.", max_length=50),
        ),
        migrations.AlterField(
            model_name='paymentaka',
            name='member',
            field=models.ForeignKey(to='members.Member', help_text='The member who has payments under another name.'),
        ),
    ]
