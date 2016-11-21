# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations



class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('payment', '0002_bankpayment_reversal'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankpayment',
            name='invoice_object_content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bankpayment',
            name='invoice_object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
