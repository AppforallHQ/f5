# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import plans.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.IntegerField(validators=[plans.models.neg_validator])),
                ('expires_at', models.DateTimeField()),
                ('paid', models.BooleanField(default=False)),
                ('pay_time', models.DateTimeField(null=True, blank=True)),
                ('expired', models.BooleanField(default=False)),
                ('invalid', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.IntegerField(validators=[plans.models.non_zero_validator])),
                ('period_length', models.FloatField(validators=[plans.models.non_zero_validator])),
                ('overdue_length', models.FloatField()),
                ('preinvoice_length', models.FloatField()),
                ('invoice_expiration_length', models.IntegerField()),
                ('interaction_endpoint_url', models.TextField()),
                ('successful_payment_endpoint_url', models.TextField()),
                ('fail_payment_endpoint_url', models.TextField()),
                ('mail_endpoint_url', models.TextField()),
                ('label', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=128)),
                ('partner', models.CharField(max_length=128)),
                ('used', models.BooleanField(default=False)),
                ('assigned_mail', models.CharField(default=None, max_length=256, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PromoType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=128)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PromoTypePlanDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('final_price', models.IntegerField()),
                ('plan', models.ForeignKey(to='plans.Plan')),
                ('promo_type', models.ForeignKey(to='plans.PromoType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=1, choices=[(1, b'New'), (2, b'Active'), (3, b'Pre-Invoice'), (4, b'Overdue'), (5, b'Deactive')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateTimeField(null=True, blank=True)),
                ('uuid', models.TextField()),
                ('email', models.EmailField(max_length=75)),
                ('user_id', models.CharField(default=None, max_length=64, null=True)),
                ('plan', models.ForeignKey(to='plans.Plan')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('uuid', 'plan')]),
        ),
        migrations.AlterUniqueTogether(
            name='promotypeplandetail',
            unique_together=set([('promo_type', 'plan')]),
        ),
        migrations.AddField(
            model_name='promocode',
            name='promo_type',
            field=models.ForeignKey(to='plans.PromoType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invoice',
            name='promo_code',
            field=models.ForeignKey(default=None, blank=True, to='plans.PromoCode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invoice',
            name='subscription',
            field=models.ForeignKey(to='plans.Subscription'),
            preserve_default=True,
        ),
    ]
