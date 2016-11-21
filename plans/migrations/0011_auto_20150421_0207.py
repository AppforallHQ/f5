# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import plans.models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0010_auto_20150421_0159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='subscription',
            field=plans.models._ForeignKey(to='plans.Subscription'),
        ),
    ]
