# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0013_membershippayment'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentAKA',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('aka', models.CharField(max_length=50, help_text='The AKA (probably a simple variation on their name).')),
                ('member', models.ForeignKey(to='members.Member', help_text='The member who has an AKA.', related_name='akas')),
            ],
            options={
                'verbose_name': 'Membership AKA',
            },
        ),
        migrations.RemoveField(
            model_name='memberaka',
            name='member',
        ),
        migrations.RemoveField(
            model_name='membershippayment',
            name='paying_member',
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='paid_by_member',
            field=models.DecimalField(decimal_places=2, max_digits=6, help_text='The full amount paid by the member, including payment processing fee IF THEY PAID IT.', default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='payer_email',
            field=models.EmailField(max_length=40, help_text='No need to provide this if member was linked above.', blank=True),
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='payer_name',
            field=models.CharField(max_length=40, help_text='No need to provide this if member was linked above.', blank=True),
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='payment_date',
            field=models.DateField(null=True, help_text='The date on which the payment was made. Can be blank if unknown.', blank=True),
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='payment_method',
            field=models.CharField(choices=[('$', 'Cash'), ('C', 'Check'), ('S', 'Square'), ('2', '2Checkout'), ('W', 'WePay'), ('P', 'PayPal')], max_length=1, help_text='The payment method used.', default='$'),
        ),
        migrations.AddField(
            model_name='membershipterm',
            name='processing_fee',
            field=models.DecimalField(decimal_places=2, max_digits=6, help_text="Payment processor's fee, regardless of whether it was paid by the member or Xerocraft.", default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='membershipterm',
            name='member',
            field=models.ForeignKey(related_name='terms', null=True, on_delete=django.db.models.deletion.PROTECT, help_text='The member who made the payment.', to='members.Member', blank=True, default=None),
        ),
        migrations.DeleteModel(
            name='MemberAKA',
        ),
        migrations.DeleteModel(
            name='MembershipPayment',
        ),
    ]
