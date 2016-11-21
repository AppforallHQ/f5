from celery import task
from django.utils import timezone
from datetime import timedelta

import requests
import json

class EndpointNotAvailabe(Exception):
    pass

def call_external_endpoint_to_update_status(the_task, action, subscription):
    payload = {"uuid": subscription.uuid,
               "plan": subscription.plan.pk,
               "activate": (action == "activate"),
              }

    response = requests.put(
        subscription.plan.interaction_endpoint_url % payload,
        data=json.dumps(payload))

    if response.status_code != 200:
        e = EndpointNotAvailabe()
        raise the_task \
            .retry(args=[subscription], exc=e)
    else:
        return True

@task
def send_invoice_notification(invoice, email_type, **kwargs):
    return
    import requests

    payload = {
        "invoice_payment_url": invoice.payment_url,
        "email_type": email_type,
        "uuid": invoice.subscription.uuid,
        "plan": invoice.subscription.plan.pk,
    }

    mail_body_response = requests.post(
        invoice.subscription.plan.mail_endpoint_url % payload,
        data=json.dumps(payload))

    params = json.loads(mail_body_response.text)

    from .actions import send_mail
    send_mail(invoice, params, email_type)

@task(default_retry_delay=3*60)
def activate_subscription(subscription, **kwargs):
    pass#return call_external_endpoint_to_update_status(activate_subscription, "activate", subscription)

@task(default_retry_delay=3*60)
def deactivate_subscription(subscription, **kwargs):
    return call_external_endpoint_to_update_status(deactivate_subscription, "deactivate", subscription)

@task
def send_preinvoice():
    from plans.models import Subscription
    # FIXME
    for subscription in Subscription.objects.filter():
        if subscription.due_date < timezone.now() + timedelta(days=subscription.plan.preinvoice_length) \
        and subscription.status == Subscription.ACTIVE:
            subscription.status = Subscription.PREINVOICE
            subscription.full_clean()
            subscription.save()

@task
def mark_subscriptions_as_overdue():
    from plans.models import Subscription
    # FIXME
    for subscription in Subscription.objects.filter():
        if subscription.due_date < timezone.now() and subscription.status == Subscription.PREINVOICE:
            subscription.status = Subscription.OVERDUE
            subscription.full_clean()
            subscription.save()

@task
def end_gracetime_for_fucking_users():
    from plans.models import Subscription
    # FIXME
    for subscription in Subscription.objects.filter():
        if subscription.due_date + timedelta(days=subscription.plan.overdue_length) < timezone.now():
            subscription.status = Subscription.DEACTIVE
            subscription.full_clean()
            subscription.save()

@task
def invalidate_invoices():
    from plans.models import Invoice
    # FIXME
    for invoice in Invoice.objects.filter():
        if invoice.expires_at < timezone.now():
            invoice.mark_as_invalid()
