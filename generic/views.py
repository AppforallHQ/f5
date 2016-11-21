
# -*- coding: utf-8 -*-

from django.shortcuts import render
from tokenapi.decorators import token_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied,ValidationError
from django.http import HttpResponse,HttpResponseBadRequest,HttpResponseRedirect,Http404
from functools import wraps
from plans.models import Subscription, Plan, Invoice , PromoCode , PromoType, PromoTypePlanDetail,ItemInvoice
from .models import GenericInvoice
from payment.models import BankPayment
import json,time
from django.utils import timezone
import requests
import logging
from django.shortcuts import get_object_or_404
import analytics
import apiv2.views

logging.basicConfig(filename='/var/log/f5/generic.log', level=logging.INFO)
@token_required
def initialize(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        email = request.POST.get("email",None)
        amount = request.POST.get("amount",None)
        callback_token = request.POST.get("callback_token",None)
        callback_url = request.POST.get("callback_url",None)
        metadata = json.loads(request.POST.get("metadata","{}"))
        if not amount or not amount.isdigit() or not email or not callback_token or not callback_url:
            return HttpResponseBadRequest(json.dumps({"error":True}))
        request.session['callback'] = {'token' : callback_token,'url' : callback_url}
        request.session['user_id'] = request.POST.get("user_id",None)
        request.session['user_mail'] = email
        request.session['genericinvoice'] = GenericInvoice(amount=int(amount),
                                        original_amount=int(amount),
                                        paid=False,metadata=metadata)

        request.session.set_expiry(0)

        return HttpResponse(json.dumps({"success":True,"token":request.session.session_key}))


    raise PermissionDenied()

@token_required
def payment(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser and request.session.get("genericinvoice",None):                
            gateway = request.POST.get('gateway')

            from plans.views import invoice_checkout
            return invoice_checkout(request,gateway)
    except:
        import sys
        print sys.exc_info()
    raise PermissionDenied()


def payment_callback(session,request=None):
    callback = session['callback']
    logger = logging.getLogger("Generic Invoice Payment Result")
    try:
        if session['transaction'].successful_payment and str(session['transaction'].res_code) == "0":
            invoice = session['genericinvoice']
            invoice.full_clean()
            invoice.save()
            invoice.post_paid_actions()
            sales_reference_id = '-'
            if "payment" in session:
                session["payment"].invoice = invoice
                session["payment"].user_id = session['user_id']
                session["payment"].save()
                sales_reference_id = session['payment'].sale_reference_id
            transaction = session['transaction']
            transaction.hamkharid_object = invoice
            transaction.full_clean()
            transaction.save()
        
            
            r = requests.post(callback['url'],data={'success':True,'sales_reference_id':sales_reference_id,'invoice_id':invoice.pk,'tokenback':callback['token'],'token':session.session_key})
            logger.info(r.text)
            js = r.json()
            if(js['success']):
                session.flush()
                return HttpResponseRedirect(js['redirect'])
            else:
                return HttpResponse("خطا در ارسال اطلاعات. پرداخت شما با موفقیت ثبت شده است. جهت پیگیری با پشتیبانی تماس بگیرید.")
    except:
        import sys
        print sys.exc_info()
        import traceback
        traceback.print_exc()
        logger.info(sys.exc_info())
    try:
        r = requests.post(callback['url'],data={'error':True,'res_code':session['transaction'].res_code,'tokenback':callback['token'],'token':session.session_key})
        print r.text
        js = r.json()
        if "inner_error_page" in js:
            request.POST = js
            return apiv2.views.general_error_page(request)
        return HttpResponseRedirect(js['redirect'])
    except:
        import sys
        logger.info(sys.exc_info())
    return HttpResponse(u"خطا در ارسال اطلاعات به پذیرنده")


