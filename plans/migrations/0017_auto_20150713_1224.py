# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import plans.models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0016_auto_20150621_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotypeplandetail',
            name='discount',
            field=plans.models.PercentField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='promotypeplandetail',
            name='final_price',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
