# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0006_settings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='settings',
            options={'verbose_name_plural': 'Settings'},
        ),
        migrations.AddField(
            model_name='settings',
            name='CAMPAIGN_PROMO_PARTNER',
            field=models.CharField(default=b'\xda\xa9\xd9\x85\xd9\xbe\xdb\x8c\xd9\x86\xe2\x80\x8c\xd9\x87\xd8\xa7\xdb\x8c \xd9\x88\xdb\x8c\xda\x98\xd9\x87', max_length=50, verbose_name=b'Campaign promo partner'),
        ),
        migrations.AddField(
            model_name='settings',
            name='REFERRED_GETS_PROMO',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='settings',
            name='USERS_GETS_PROMO',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='settings',
            name='OMGPAY_DISABLE_FOR_USERS',
            field=models.BooleanField(default=False, verbose_name=b'Disable payment gateway for users'),
        ),
    ]
