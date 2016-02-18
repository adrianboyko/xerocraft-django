# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0028_auto_20160218_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='membership_type',
            field=models.CharField(default='R', help_text='The type of membership.', choices=[('R', 'Regular'), ('W', 'Work-Trade'), ('S', 'Scholarship'), ('C', 'Complimentary'), ('G', 'Group')], max_length=1),
        ),
    ]
