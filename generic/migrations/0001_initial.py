# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import generic.models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GenericInvoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.IntegerField(validators=[generic.models.neg_validator])),
                ('original_amount', models.IntegerField(validators=[generic.models.neg_validator])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid', models.BooleanField(default=False)),
                ('pay_time', models.DateTimeField(null=True, blank=True)),
                ('invalid', models.BooleanField(default=False)),
                ('ref_key', models.CharField(default=None, max_length=64, null=True, blank=True)),
                ('metadata', jsonfield.fields.JSONField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
