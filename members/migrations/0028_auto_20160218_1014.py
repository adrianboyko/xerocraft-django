# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
        ('members', '0027_auto_20160215_1813'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('membership_type', models.CharField(default='R', max_length=1, help_text='The type of membership.', choices=[('R', 'Regular'), ('W', 'Work-Trade'), ('S', 'Scholarship'), ('C', 'Complimentary')])),
                ('family_count', models.IntegerField(default=0, help_text='The number of ADDITIONAL family members included in this membership. Usually zero.')),
                ('start_date', models.DateField(help_text='The frist day on which the membership is valid.')),
                ('end_date', models.DateField(help_text='The last day on which the membership is valid.')),
                ('protected', models.BooleanField(default=False, help_text='Protect against further auto processing by ETL, etc. Prevents overwrites of manually enetered data.')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=None, blank=True, to='members.Member', help_text='The member to whom this membership applies.', null=True)),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='books.Sale', help_text='The sale that includes this line item.', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MembershipGiftCardRedemption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('redemption_date', models.DateField(default=django.utils.timezone.now, help_text='The date on which the gift card was redeemed.')),
            ],
            options={
                'verbose_name': 'Gift card redemption',
            },
        ),
        migrations.CreateModel(
            name='MembershipGiftCardReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
            ],
            options={
                'verbose_name': 'Membership gift card',
            },
        ),
        migrations.RemoveField(
            model_name='donationlineitem',
            name='purchase',
        ),
        migrations.RemoveField(
            model_name='membershipgiftcardlineitem',
            name='card',
        ),
        migrations.RemoveField(
            model_name='membershipgiftcardlineitem',
            name='purchase',
        ),
        migrations.RemoveField(
            model_name='paymentaka',
            name='member',
        ),
        migrations.AlterModelOptions(
            name='memberlogin',
            options={'verbose_name': 'Login'},
        ),
        migrations.AlterModelOptions(
            name='membershipgiftcard',
            options={'verbose_name': 'Gift card'},
        ),
        migrations.AlterModelOptions(
            name='paidmembershipnudge',
            options={'verbose_name': 'Renewal reminder'},
        ),
        migrations.DeleteModel(
            name='DonationLineItem',
        ),
        migrations.DeleteModel(
            name='MembershipGiftCardLineItem',
        ),
        migrations.DeleteModel(
            name='PaymentAKA',
        ),
        migrations.DeleteModel(
            name='Purchase',
        ),
        migrations.AddField(
            model_name='membershipgiftcardreference',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='members.MembershipGiftCard', help_text='The membership gift card being sold.'),
        ),
        migrations.AddField(
            model_name='membershipgiftcardreference',
            name='purchase',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='books.Sale', help_text='The sale that includes this line item.', null=True),
        ),
        migrations.AddField(
            model_name='membershipgiftcardredemption',
            name='card',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='members.MembershipGiftCard', help_text='The membership gift card that was redeemed.'),
        ),
        migrations.AddField(
            model_name='membership',
            name='redemption',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='members.MembershipGiftCardRedemption', help_text='The associated membership gift card redemption, if any. Usually none.', null=True),
        ),
    ]
