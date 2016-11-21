# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import plans.models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0007_auto_20150330_0046'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemInvoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.IntegerField(validators=[plans.models.neg_validator])),
                ('plan_amount', models.IntegerField(validators=[plans.models.neg_validator])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid', models.BooleanField(default=False)),
                ('pay_time', models.DateTimeField(null=True, blank=True)),
                ('invalid', models.BooleanField(default=False)),
                ('metadata', jsonfield.fields.JSONField()),
                ('generated_promo_code', models.ForeignKey(related_name='+', to='plans.PromoCode')),
                ('plan', models.ForeignKey(to='plans.Plan', null=True)),
                ('promo_code', models.ForeignKey(default=None, blank=True, to='plans.PromoCode', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='giftinvoice',
            name='generated_promo_code',
        ),
        migrations.RemoveField(
            model_name='giftinvoice',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='giftinvoice',
            name='promo_code',
        ),
        migrations.DeleteModel(
            name='GiftInvoice',
        ),
    ]
