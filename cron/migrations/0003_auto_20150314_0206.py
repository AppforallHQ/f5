# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cron', '0002_auto_20150203_0734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cronlog',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, b'Active'), (2, b'invoice_issued'), (3, b'plan_ending_notice'), (4, b'extra_day_notice'), (5, b'suspend_idevice'), (6, b'Blocked')]),
            preserve_default=True,
        ),
    ]
