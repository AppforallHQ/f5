# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0008_auto_20150401_2155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iteminvoice',
            name='generated_promo_code',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to='plans.PromoCode', null=True),
            preserve_default=True,
        ),
    ]
