# Generated by Django 2.0.3 on 2018-08-15 03:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kmkr', '0022_remove_underwritingspots_holds_donation'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='broadcast',
            unique_together={('episode', 'date', 'type')},
        ),
    ]
