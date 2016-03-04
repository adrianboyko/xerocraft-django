# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import members.models
import uuid


def gen_ctrlid(apps, schema_editor):
    m = apps.get_model('members', 'Membership')
    for row in m.objects.all():
        row.ctrlid = str(uuid.uuid4()).replace('-', '')
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0040_auto_20160303_1716'),
    ]

    operations = [
        migrations.RunPython(gen_ctrlid),
    ]
