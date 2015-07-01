# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0018_remove_member_family_anchor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Worker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('auth_user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, to='tasks.Tag')),
            ],
        ),
        migrations.AddField(
            model_name='claim',
            name='claimer',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='eligible_claimants2',
            field=models.ManyToManyField(related_name='claimable_TaskTemplates', blank=True, help_text='Anybody chosen is eligible to claim the task.<br/>', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='owner2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text='The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.', related_name='owned_TaskTemplates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='reviewer2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text='If required, a member who will review the work once its completed.', related_name='reviewableTaskTemplates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='recurringtasktemplate',
            name='uninterested2',
            field=models.ManyToManyField(related_name='uninteresting_TaskTemplates', blank=True, help_text='People that are not interested in this item.', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='claimant2',
            field=models.ManyToManyField(related_name='tasks_claimed', to=settings.AUTH_USER_MODEL, through='tasks.Claim'),
        ),
        migrations.AddField(
            model_name='task',
            name='eligible_claimants2',
            field=models.ManyToManyField(related_name='claimable_Tasks', blank=True, help_text='Anybody chosen is eligible to claim the task.<br/>', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='owner2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text='The member that asked for this task to be created or has taken responsibility for its content.<br/>This is almost certainly not the person who will claim the task and do the work.', related_name='owned_Tasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='reviewer2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, help_text='If required, a member who will review the work once its completed.', related_name='reviewableTasks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='uninterested2',
            field=models.ManyToManyField(related_name='uninteresting_Tasks', blank=True, help_text='People that are not interested in this item.', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='workers2',
            field=models.ManyToManyField(related_name='tasks_worked', to=settings.AUTH_USER_MODEL, through='tasks.Work'),
        ),
        migrations.AddField(
            model_name='tasknote',
            name='author2',
            field=models.ForeignKey(null=True, blank=True, help_text='The member who wrote this note.', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='work',
            name='worker2',
            field=models.ForeignKey(default=None, help_text='Person that did work toward completing task.', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
