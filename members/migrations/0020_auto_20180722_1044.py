# Generated by Django 2.0.3 on 2018-07-22 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0019_auto_20180422_1221'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='active',
            field=models.BooleanField(default=True, help_text='Indicates whether a tag should be used when entering new data. Only use active tags.'),
        ),
        migrations.AlterField(
            model_name='groupmembership',
            name='group_tag',
            field=models.ForeignKey(help_text='Group membership is initially populated with the set of people having this tag.', limit_choices_to={'active': True}, on_delete=django.db.models.deletion.PROTECT, to='members.Tag'),
        ),
    ]
