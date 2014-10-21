# flake8: noqa
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Stand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(default='', max_length=256, null=True, blank=True)),
                ('hostname', models.CharField(max_length=256, db_index=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('css', models.TextField(default='', null=True, blank=True)),
                ('description', models.TextField(default='', null=True, blank=True)),
                ('access', models.CharField(default=b'open', max_length=256, choices=[(b'open', b'Open Access'), (b'login', b'Logged-in Users Only'), (b'group', b'Users in Selected Group(s) Only'), (b'whitelist', b'Whitelisted Users Only')])),
                ('gated', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandAvailablePageBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('block', models.CharField(max_length=256, db_index=True)),
                ('stand', models.ForeignKey(to='main.Stand')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access', models.CharField(default=b'student', max_length=16)),
                ('group', models.ForeignKey(to='auth.Group')),
                ('stand', models.ForeignKey(to='main.Stand')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, db_index=True)),
                ('value', models.CharField(max_length=256)),
                ('stand', models.ForeignKey(to='main.Stand')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StandUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access', models.CharField(default=b'student', max_length=16)),
                ('stand', models.ForeignKey(to='main.Stand')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user__last_name', 'user__first_name'),
            },
            bases=(models.Model,),
        ),
    ]
