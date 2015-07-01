# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0020_auto_20150618_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='membership_card_seq',
            field=models.IntegerField(default=0, help_text='Incrementing the membership card sequence number invalidates any existing membership cards with a lower sequence number.'),
        ),
        migrations.AlterField(
            model_name='member',
            name='auth_user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, help_text='This must point to the corresponding auth.User object.'),
        ),
    ]
