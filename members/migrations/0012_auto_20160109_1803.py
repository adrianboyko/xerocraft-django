# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0011_membershippayment'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberAKA',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('aka', models.CharField(max_length=50, help_text='The AKA (probably a simple variation on their name).')),
                ('member', models.ForeignKey(to='members.Member', help_text='The member who has an AKA.', related_name='akas')),
            ],
        ),
        migrations.CreateModel(
            name='MembershipTerm',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('membership_type', models.CharField(choices=[('R', 'Regular'), ('W', 'Work-Trade')], default='R', help_text='The type of membership.', max_length=1)),
                ('family_count', models.IntegerField(default=0, help_text='The number of ADDITIONAL family members included in this membership. Usually zero.')),
                ('start_date', models.DateField(help_text='The frist day on which the membership is valid.')),
                ('end_date', models.DateField(help_text='The last day on which the membership is valid.')),
                ('member', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, help_text='The member who made the payment.', to='members.Member', null=True, related_name='terms')),
            ],
        ),
        migrations.RemoveField(
            model_name='membershippayment',
            name='paying_member',
        ),
        migrations.DeleteModel(
            name='MembershipPayment',
        ),
    ]
