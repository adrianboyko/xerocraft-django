# Generated by Django 2.0.3 on 2018-04-07 20:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_auto_20180405_1233'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worker',
            name='last_work_mtd_reported',
        ),
    ]