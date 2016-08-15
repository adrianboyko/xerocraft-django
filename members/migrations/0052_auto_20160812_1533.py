# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0051_auto_20160604_2137'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='paidmembership',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='paidmembership',
            name='member',
        ),
        migrations.AlterField(
            model_name='member',
            name='membership_card_md5',
            field=models.CharField(null=True, blank=True, max_length=32, help_text='MD5 of the random urlsafe base64 string on the membership card.'),
        ),
        migrations.DeleteModel(
            name='PaidMembership',
        ),
    ]
