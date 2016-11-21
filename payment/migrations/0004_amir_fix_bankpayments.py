# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from django.apps import apps
from django.contrib.contenttypes.management import update_contenttypes

def update_all_contenttypes(**kwargs):
    for app_config in apps.get_app_configs():
        update_contenttypes(app_config, **kwargs)

def forward_function(apps,schema_editor):
    update_all_contenttypes() 
    ContentType = apps.get_model("contenttypes", "ContentType")
    
    invoice_contenttype = ContentType.objects.get(app_label='plans',model='invoice')

    BankPayment = apps.get_model("payment", "BankPayment")
    for trans in BankPayment.objects.all():
        if trans.invoice:
            trans.invoice_object_content_type = invoice_contenttype
            trans.invoice_object_id = trans.invoice.pk
        else:
            trans.invoice_object = None
        trans.save()

def backward_function(apps,schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('plans', '0005_auto_20150203_0514'),
        ('payment', '0002_bankpayment_reversal'),
        ('payment', '0003_auto_20150324_1349'),
    ]

    operations = [
        migrations.RunPython(
            forward_function,backward_function
        ),
    ]