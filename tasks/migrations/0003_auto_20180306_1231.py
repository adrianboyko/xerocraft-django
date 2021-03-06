# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-06 19:31
from __future__ import unicode_literals

import abutils.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0012_auto_20180205_0948'),
        ('tasks', '0002_auto_20171123_1110'),
    ]

    operations = [
        migrations.CreateModel(
            name='EligibleClaimant2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('1ST', 'Default Claimant'), ('2ND', 'Eligible, 2nd String'), ('3RD', 'Eligible, 3rd String'), ('DEC', 'Will No Claim')], help_text='The type of this relationship.', max_length=3)),
                ('should_nag', models.BooleanField(default=True, help_text='If true, member may receive email concerning the related task.')),
                ('member', models.ForeignKey(help_text='The member in this relation.', on_delete=django.db.models.deletion.CASCADE, to='members.Member')),
            ],
        ),
        migrations.CreateModel(
            name='TemplateEligibleClaimants2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('1ST', 'Default Claimant'), ('2ND', 'Eligible, 2nd String'), ('3RD', 'Eligible, 3rd String')], help_text='The type of this relationship.', max_length=3)),
                ('should_nag', models.BooleanField(default=False, help_text='If true, member will be encouraged to work instances of the template.')),
                ('member', models.ForeignKey(help_text='The member in this relation.', on_delete=django.db.models.deletion.CASCADE, to='members.Member')),
            ],
        ),
        migrations.RemoveField(
            model_name='recurringtasktemplate',
            name='eligible_tags',
        ),
        migrations.RemoveField(
            model_name='task',
            name='eligible_tags',
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='anybody_is_eligible',
            field=models.BooleanField(default=False, help_text='Indicates whether the task is workable by ANYBODY. Use sparingly!'),
        ),
        migrations.AddField(
            model_name='task',
            name='anybody_is_eligible',
            field=models.BooleanField(default=False, help_text='Indicates whether the task is workable by ANYBODY. Use sparingly!'),
        ),
        migrations.AlterField(
            model_name='work',
            name='witness',
            field=models.ForeignKey(blank=True, help_text='A director or officer that witnessed the work.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='members.Member'),
        ),
        migrations.AlterField(
            model_name='work',
            name='work_duration',
            field=models.DurationField(blank=True, help_text='Time spent working the task. Only blank if work is in progress or worker forgot to check out.', null=True, validators=[abutils.validators.positive_duration]),
        ),
        migrations.AddField(
            model_name='templateeligibleclaimants2',
            name='template',
            field=models.ForeignKey(help_text='The task in this relation.', on_delete=django.db.models.deletion.CASCADE, to='tasks.RecurringTaskTemplate'),
        ),
        migrations.AddField(
            model_name='eligibleclaimant2',
            name='task',
            field=models.ForeignKey(help_text='The task in this relation.', on_delete=django.db.models.deletion.CASCADE, to='tasks.Task'),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='eligible_claimants_2',
            field=models.ManyToManyField(blank=True, help_text='Anybody chosen is eligible to claim the task.<br/>', related_name='claimable2_recurringtasktemplate', through='tasks.TemplateEligibleClaimants2', to='members.Member'),
        ),
        migrations.AddField(
            model_name='task',
            name='eligible_claimants_2',
            field=models.ManyToManyField(blank=True, help_text='Anybody chosen is eligible to claim the task.<br/>', related_name='claimable_tasks', through='tasks.EligibleClaimant2', to='members.Member'),
        ),
    ]
