# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0017_auto_20150713_1224'),
        ('payment', '0007_auto_20150716_1954'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='CAMPAIGN_PROMO_TYPE',
            field=models.ForeignKey(related_name='Campaign', verbose_name=b'Current campaign promo type', blank=True, to='plans.PromoType', null=True),
        ),
        migrations.AddField(
            model_name='settings',
            name='REFERRED_PROMO_TYPE',
            field=models.ForeignKey(related_name='Referred', blank=True, to='plans.PromoType', null=True),
        ),
    ]
