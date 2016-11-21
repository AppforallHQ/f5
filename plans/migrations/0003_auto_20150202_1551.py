# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from datetime import timedelta


def active_invoice(sub):
    invoice = [f for f in sub.invoice_set.all().order_by('-expires_at')][0]
    return invoice

def forward_function(apps,schema_editor):
    Subscription = apps.get_model("plans", "Subscription")
    Invoice = apps.get_model("plans", "Invoice")
    for invoice in Invoice.objects.all():
        if active_invoice(invoice.subscription) and invoice.pk == active_invoice(invoice.subscription).pk:
            if not invoice.subscription.due_date:
                continue
            invoice.created_at = invoice.expires_at-timedelta(days = invoice.subscription.plan.period_length)
            invoice.expires_at = invoice.subscription.due_date
            invoice.started_at = invoice.expires_at-timedelta(days = invoice.subscription.plan.period_length)
        else:
            if not invoice.expires_at:
                invoice.expires_at = invoice.subscription.due_date-timedelta(days = invoice.subscription.plan.period_length + 1)
            invoice.created_at = invoice.expires_at-timedelta(days = invoice.subscription.plan.period_length)
            invoice.started_at = invoice.created_at
        invoice.plan = invoice.subscription.plan
        invoice.plan_amount = invoice.subscription.plan.price
        invoice.save()




class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0002_auto_20150131_1549'),
    ]

    operations = [
        migrations.RunPython(
            forward_function,
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('uuid',)]),
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='plan',
        ),
    ]
