# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import books.models
import uuid


def gen_ctrlid(apps, schema_editor):
    MonetaryDonation = apps.get_model('books', 'MonetaryDonation')
    for row in MonetaryDonation.objects.all():
        row.ctrlid = str(uuid.uuid4()).replace("-", "")
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0013_auto_20160304_2228'),
    ]

    operations = [
        migrations.RunPython(gen_ctrlid),
    ]
