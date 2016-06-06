# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_shop_tool_toolissue_toolissuenote'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='info_link',
        ),
        migrations.AddField(
            model_name='shop',
            name='public_info',
            field=models.URLField(help_text='A link to the public wiki page about this shop.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='public_info',
            field=models.URLField(help_text='A link to the public wiki page about this tool.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='status',
            field=models.CharField(help_text='Status of the tool. If DEGRADED or UNUSABLE see Tool Issues.', choices=[('G', 'Good'), ('D', 'Degraded'), ('U', 'Unusable')], default='G', max_length=1),
        ),
        migrations.AlterField(
            model_name='toolissue',
            name='status',
            field=models.CharField(help_text='Status of the issue. Set to CLOSED if issue is invalid or if the issue has been dealt with.', choices=[('N', 'New Issue'), ('V', 'Validated'), ('C', 'Closed')], default='N', max_length=1),
        ),
    ]
