# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import plans.models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0006_auto_20150314_0206'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftInvoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.IntegerField(validators=[plans.models.neg_validator])),
                ('plan_amount', models.IntegerField(validators=[plans.models.neg_validator])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid', models.BooleanField(default=False)),
                ('pay_time', models.DateTimeField(null=True, blank=True)),
                ('invalid', models.BooleanField(default=False)),
                ('giver_id', models.CharField(default=None, max_length=64, null=True)),
                ('getter_id', models.CharField(default=None, max_length=64, null=True)),
                ('giver_email', models.CharField(default=None, max_length=256, null=True)),
                ('getter_email', models.CharField(default=None, max_length=256, null=True)),
                ('generated_promo_code', models.ForeignKey(related_name='+', to='plans.PromoCode')),
                ('plan', models.ForeignKey(to='plans.Plan', null=True)),
                ('promo_code', models.ForeignKey(default=None, blank=True, to='plans.PromoCode', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='promocode',
            index_together=set([('code',)]),
        ),
    ]
