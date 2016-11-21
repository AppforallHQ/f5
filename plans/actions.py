import analytics
import requests, json

import tasks

def send_new_invoice_notification(invoice):
    tasks.send_invoice_notification.delay(invoice, "new_invoice_notification")

def send_successful_invoice_payment_email(invoice):
    tasks.send_invoice_notification.delay(invoice, "successful_payment")

def send_mail(invoice, params, email_type):
    to = invoice.subscription.email

    analytics.identify(user_id=to, traits={
        'email': to,
    })

    due_date = invoice.subscription.due_date
    if due_date:
        due_date = due_date.isoformat()
    else:
        'No duedate specified'

    properties = {
        'params': params,
        'subscription': {
            'due_date': due_date,
        },
        'invoice': invoice
    }
    analytics.track(user_id=to, event=email_type, properties=properties)

    print properties
    print "OMG MAIL SENT!"
