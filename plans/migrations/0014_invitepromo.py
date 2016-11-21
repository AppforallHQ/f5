# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0013_auto_20150503_0355'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitePromo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('giver_email', models.EmailField(max_length=254)),
                ('getter_email', models.EmailField(max_length=254)),
                ('getter_promo', models.ForeignKey(related_name='getter_promo', to='plans.PromoCode')),
                ('giver_promo', models.ForeignKey(related_name='giver_promo', to='plans.PromoCode')),
            ],
        ),
    ]
