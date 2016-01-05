# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_auto_20151012_1240'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitevent',
            name='method',
            field=models.CharField(choices=[('R', 'RFID'), ('F', 'Front Desk'), ('M', 'Mobile App'), ('U', 'Unknown')], default='U', help_text="The method used to record the visit, such as 'Front Desk' or 'RFID'.", max_length=1),
        ),
    ]
