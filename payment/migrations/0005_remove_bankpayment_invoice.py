# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_amir_fix_bankpayments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankpayment',
            name='invoice',
        ),
    ]
