# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0012_auto_20150421_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]
