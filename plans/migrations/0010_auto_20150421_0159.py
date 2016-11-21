# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import plans.models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0009_auto_20150402_1115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='email',
            field=models.EmailField(max_length=254),
        ),
    ]
