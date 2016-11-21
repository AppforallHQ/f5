# -*- coding: utf-8 -*-
from django.http import HttpResponse

from .models import Invoice, PromoCode, PromoTypePlanDetail, InvitePromo
from django.core.urlresolvers import reverse

from payment.views import checkout, payment_result, create_redirect_page

from django.shortcuts import redirect
from django.conf import settings

import json,apiv2.views,generic.views

from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError

from django.http import HttpResponseBadRequest, Http404,HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from payment.models import BankPayment

import requests
from requests.auth import HTTPBasicAuth

def invoice_checkout(request, gateway):
    if request.session.get('subscription',None):
        invoice = request.session.get('invoice',None)
    elif request.session.get('genericinvoice',None):
        invoice = request.session.get('genericinvoice',None)
    else:
        invoice = request.session.get('giftinvoice',None)
    print "Amount",invoice.amount
    try:
        failAddress = invoice.plan.fail_payment_endpoint_url
    except:
        failAddress = "" # I'm not so sure about this
    local_uri = reverse(invoice_payment_result, kwargs={"gateway": gateway})
    redirectAddress = request.build_absolute_uri(local_uri)


    if invoice.status == "active":
        amount = invoice.amount
        return checkout(request, redirectAddress, invoice, amount, gateway,failAddress)
    else:
        raise Http404


@csrf_exempt
def invoice_payment_result(request, gateway):
    
    try:
        if "additionalData" in request.POST:
            token = request.POST.get("additionalData",None)
            import payment.views
            token = payment.views.retrieve_session_key(token)
            from importlib import import_module
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore(token)
            assert session.get('subscription',None) or session.get('giftinvoice',None) or session.get('genericinvoice',None)
        elif "SaleOrderId" in request.POST:
            invoice_id = request.POST.get("SaleOrderId")
            pay = BankPayment.objects.get(gateway=gateway,invoice_number=invoice_id)
            
            from importlib import import_module
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore(pay.session_key)
            session["payment"] = pay
            assert session.get('subscription',None) or session.get('giftinvoice',None) or session.get('genericinvoice',None)
        else:
            raise PermissionDenied()
            
    except Exception as e:
        print e
        raise PermissionDenied()
    
    session["post"] = request.POST
    
    withdrawal = payment_result(session, gateway)
    session["post"] = None
    invoice = withdrawal.hamkharid_object

    if withdrawal.successful_payment == True:
        if invoice.paid == False:
            invoice.paid = True
    session["transaction"] = withdrawal
    session["invoice"] = invoice
    if session.get('invoice_payment',None) == True:
        return apiv2.views.invoice_payment_back(session,request)
    elif session.get('giftinvoice',None):
        return apiv2.views.gift_finalize_payment(session,request)
    elif session.get('genericinvoice',None):
        return generic.views.payment_callback(session,request)
    return apiv2.views.finalizepayment(session,request)



def api_create_redirect_page(request,data):
    return create_redirect_page(request,data)


def validateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def validatePromoInvite(promo):
    """Check if promo is able to invite with discount and it's not used before

    """
    valid_types = [VALID_PROMO_TYPES]
    try:
        promo_obj = PromoCode.objects.get(code=promo)
        promo_type = promo_obj.promo_type.label
        promo_used = InvitePromo.objects.get_or_none(giver_promo=promo_obj)
        if promo_type in valid_types and not promo_used:
            return True
        else:
            raise
    except:
        return False

@csrf_exempt
def invite_promo(request):
    gift_promo_label = 'VALID_PROMO'
    gift_promo_partner = 'PROMO_NAME'
    
    getter_email = request.POST.get('getter_email', None)
    getter_name = request.POST.get('getter_name', None)
    giver_email = request.POST.get('giver_email', None)
    giver_name = request.POST.get('giver_name', None)
    promo = request.POST.get('promo', None)


    if giver_name and getter_name and \
       validatePromoInvite(promo) and \
       validateEmail(giver_email) and \
       validateEmail(getter_email) and \
       not giver_email == getter_email:
        
        giver_promo_obj = PromoCode.objects.get(code=promo)
        getter_promo_obj = PromoCode.generate(1, gift_promo_label, gift_promo_partner)[0]

        cio_auth = HTTPBasicAuth(settings.CUSTOMER_SITE_ID, settings.CUSTOMER_API_KEY)

        cio_anonymous = 'https://track.customer.io/api/v1/events'
        getter_data = {'name': 'promo_invite_getter',       # Segment name
                       'data[recipient]': getter_email,
                       'data[giver_name]': giver_name,
                       'data[getter_name]': getter_name,
                       'data[promo]': getter_promo_obj.code,}

        giver_data = {'name': 'promo_invite_giver',       # Segment name
                      'data[recipient]': giver_email,
                      'data[giver_name]': giver_name,
                      'data[getter_name]': getter_name,}

        defaults = {'getter_email': getter_email,
                    'getter_name': getter_name,
                    'getter_promo': getter_promo_obj,
                    'giver_email': giver_email,
                    'giver_name': giver_name}

        obj, created = InvitePromo.objects.get_or_create(giver_promo=giver_promo_obj,
                                                         defaults=defaults)
        if not created:
            # Thread safety response:
            return HttpResponse(json.dumps({'done': False}))

        # Send emails
        requests.post(cio_anonymous, auth=cio_auth, data=getter_data).json()
        requests.post(cio_anonymous, auth=cio_auth, data=giver_data).json()


        return HttpResponse(json.dumps({'done': True}))
    else:
        return HttpResponse(json.dumps({'done': False}))
