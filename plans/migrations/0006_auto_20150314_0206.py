# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0005_auto_20150203_0514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.IntegerField(default=1, choices=[(1, b'New'), (2, b'Active'), (3, b'Pre-Invoice'), (4, b'Overdue'), (5, b'Deactive'), (6, b'Blocked')]),
            preserve_default=True,
        ),
    ]
