# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import plans.models

class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2014, 1, 1, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='plan',
            field=models.ForeignKey(default=None,null=True, to='plans.Plan'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='plan_amount',
            field=models.IntegerField(default=15000, validators=[plans.models.neg_validator]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='started_at',
            field=models.DateTimeField(default=datetime.datetime(2014, 1, 1, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plan',
            name='is_active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='promotype',
            name='expire_date',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
