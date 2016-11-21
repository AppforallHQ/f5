# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CronLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=1, choices=[(1, b'Active'), (2, b'invoice_issued'), (3, b'plan_ending_notice'), (4, b'extra_day_notice'), (5, b'suspend_idevice')])),
                ('subscription', models.ForeignKey(to='plans.Subscription')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='cronlog',
            index_together=set([('subscription',)]),
        ),
    ]
