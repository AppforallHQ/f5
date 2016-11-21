# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0004_auto_20150203_0137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='expires_at',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='started_at',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
