# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0017_auto_20150713_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocode',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='promocode',
            name='used_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, b'New'), (7, b'Paid But Not Active'), (2, b'Active'), (3, b'Pre-Invoice'), (4, b'Overdue'), (5, b'Deactive'), (6, b'Blocked')]),
        ),
    ]
