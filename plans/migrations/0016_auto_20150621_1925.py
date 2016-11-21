# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0015_auto_20150527_1647'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitepromo',
            name='giver_promo',
            field=models.OneToOneField(related_name='giver_promo', to='plans.PromoCode'),
        ),
    ]
