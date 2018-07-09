# Generated by Django 2.0.3 on 2018-06-24 00:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_auto_20180622_1915'),
    ]

    operations = [
        migrations.AddField(
            model_name='class',
            name='rsvp_period',
            field=models.IntegerField(default=3, help_text='How many days before class date will RSVPs be accepted?'),
        ),
    ]