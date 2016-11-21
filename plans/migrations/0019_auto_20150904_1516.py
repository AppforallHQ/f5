# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0018_auto_20150827_1322'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promocode',
            name='code',
            field=models.CharField(unique=True, max_length=128),
        ),
    ]
