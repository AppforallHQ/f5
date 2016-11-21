# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0014_invitepromo'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitepromo',
            name='getter_name',
            field=models.CharField(default=b'Anonymous', max_length=40),
        ),
        migrations.AddField(
            model_name='invitepromo',
            name='giver_name',
            field=models.CharField(default=b'Anonymous', max_length=40),
        ),
    ]
