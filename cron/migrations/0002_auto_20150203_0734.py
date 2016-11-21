# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('cron', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronlog',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2014, 1, 1, 0, 0), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterIndexTogether(
            name='cronlog',
            index_together=set([('subscription', 'date')]),
        ),
    ]
