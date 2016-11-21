# -*- coding: utf-8 -*-

from tokenapi.decorators import token_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied,ValidationError
from django.http import HttpResponse,HttpResponseBadRequest,HttpResponseRedirect,Http404
from functools import wraps
from plans.models import Subscription, Plan, Invoice , PromoCode , PromoType, PromoTypePlanDetail,ItemInvoice
from payment.models import BankPayment, Settings
import json,time
from django.utils import timezone
import requests
import logging
from django.shortcuts import get_object_or_404
from dateutil import parser
import analytics

logging.basicConfig(filename='/var/log/f5/apiv2.log', level=logging.INFO)

#New API! Session-Based
@token_required
def beginsubscription(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        email = request.POST.get("email",None)
        plan = request.POST.get("plan",None)
        callback_token = request.POST.get("callback_token",None)
        callback_url = request.POST.get("callback_url",None)
        if not plan or not email or not callback_token or not callback_url:
            return HttpResponseBadRequest(json.dumps({"error":True}))
        request.session['callback'] = {'token' : callback_token,'url' : callback_url}
        request.session['subscription'] = Subscription(email=email,created_at=timezone.now())
        request.session['user_mail'] = email
        request.session['invoice'] = request.session['subscription'].create_new_invoice(plan=Plan.objects.get(id=int(plan)),commit=False)
        if 'promo_code' in request.session:
            del request.session['promo_code']
            request.session.save()
        request.session.set_expiry(0)
        
        return HttpResponse(json.dumps({"success":True,"label":request.session["invoice"].plan.label,"token":request.session.session_key,"active_invoice_payment_url":request.session['invoice'].payment_url}))
        
        
    raise PermissionDenied()


@token_required
def create_gift(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        giver_email = request.POST.get("giver_email",None)
        getter_email = request.POST.get("getter_email",None)
        plan = request.POST.get("plan",None)
        callback_token = request.POST.get("callback_token",None)
        callback_url = request.POST.get("callback_url",None)
        if not plan or not giver_email or not getter_email or not callback_token or not callback_url:
            return HttpResponseBadRequest(json.dumps({"error":True}))
        request.session['callback'] = {'token' : callback_token,'url' : callback_url}
        plan = Plan.objects.get(pk=int(plan))
        request.session['user_id'] = request.POST.get("giver_id",None)
        request.session['user_mail'] = giver_email
        request.session['giftinvoice'] = ItemInvoice(amount=plan.price,
                                        plan=plan,
                                        plan_amount=plan.price,
                                        paid=False,metadata={
                                            'giver_email' : giver_email,
                                            'getter_email': getter_email,
                                            'giver_id' : request.POST.get("giver_id",None),
                                            'getter_id' : request.POST.get("getter_id",None),
                                            'giver_name' : request.POST.get("giver_name",None),
                                            'getter_name' : request.POST.get("getter_name",None),
                                        })
        
        if 'promo_code' in request.session:
            del request.session['promo_code']
            request.session.save()
        request.session.set_expiry(0)
        
        return HttpResponse(json.dumps({"success":True,"label":request.session["giftinvoice"].plan.label,"token":request.session.session_key,"active_invoice_payment_url":request.session['giftinvoice'].payment_url}))
        
        
    raise PermissionDenied()

PROMO_CODE_ERRORS = {
    'INVALID': u'کد تخفیف وارد شده اشتباه است.',
    'USED': u'این کد پیش از این استفاده شده است.',
    'USED_BY_ANOTHER': u'این کد پیش از این توسط مشتری دیگری استفاده شده است.',
    'USED_BY_SELF': u'این کد پیش از این توسط خود شما استفاده شده است.',
    'ALREADY_IN_INVOICE': u'این کد توسط شما در یک پیش فاکتور دیگر ثبت شده است.', # TODO complete this message
    'WRONG_PLAN': u'کدی که وارد کردید برای اشتراک {} می‌باشد. لطفاً دوره اشتراک خود را تغییر دهید.',
    'EXPIRED': u'تاریخ اعتبار این کد تخفیف به پایان رسیده است.',
    'GENERAL_ERROR': u'کد تخفیف وارد شده نامعتبر است.',
}
    
def processpromocode(code,invoice):
    final_price,promo_code = None,None
    err = None
    try:
        final_price, promo_code = invoice.apply_promo_code(code)
    except PromoCode.DoesNotExist:
        err = {
            'error': True,
            'message': PROMO_CODE_ERRORS['INVALID']
        }
    except PromoTypePlanDetail.DoesNotExist:
        err = {
            'error': True,
            'message': PROMO_CODE_ERRORS['WRONG_PLAN']
        }
    except ValidationError as ex:
        if ex.code != 'WRONG_PLAN':
            err = {
                'error': True,
                'message': PROMO_CODE_ERRORS[ex.code]
            }
        else: # ex.code == 'WRONG_PLAN'
            correct_plans = u" و ".join([u"{} ماهه".format(p.plan.label) for p in ex.params['plans']])
            err = {
                'error': True,
                'message': PROMO_CODE_ERRORS[ex.code].format(correct_plans)
            }
            
    except Exception as ex:
        print ex
        err = {
            'error': True,
            'message': PROMO_CODE_ERRORS['GENERAL_ERROR']
        }
    return invoice,promo_code,final_price,err
            

@token_required
def check_promo(request):
    """ A very simple view to check promocode status
    """
    promo = request.POST.get('promo')
    response = {}
    try:
        promo_obj = PromoCode.objects.get(code=promo)
        if promo_obj.used != False:
            raise
        response["done"] = True
    except:
        response["error"] = True
    return HttpResponse(json.dumps(response), content_type="application/json")


@token_required
def applypromocode(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser:
            invoice,err = None,None
            code = request.POST['promo_code']
            if request.session.get("subscription",None):        
                invoice = request.session['invoice']
            else:
                invoice = request.session['giftinvoice']
            invoice,promo_code,final_price,err = processpromocode(code,invoice)    
            if err:
                return HttpResponse(json.dumps(err), content_type="application/json", status=200)
            if request.session.get("subscription",None): 
                request.session['invoice'] = invoice
            else:
                request.session['giftinvoice'] = invoice
            request.session['promo_code'] = promo_code
            res = {
                "success": True,
                "partner": promo_code.partner,
                "percent": 100*(1-float(final_price)/float(invoice.plan.price)),
                "final_price": final_price/10
            }
        
            return HttpResponse(json.dumps(res), content_type="application/json")
    except:
        import sys
        print sys.exc_info()
        
    raise PermissionDenied()


@token_required
def gift_start_payment(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser and request.session.get("giftinvoice",None):
            
            if "promo_code" in request.session:
                if request.session["promo_code"].assigned_mail and \
                request.session["promo_code"].assigned_mail != request.session["giftinvoice"].metadata['giver_email']:
                    request.POST=request.POST.copy()
                    request.POST["error_msg"] = u"متاسفانه کاربری با ایمیل دیگر با این کد تخفیف اقدام به ثبت نام کرده است.<br/>اگر این کد تخفیف متعلق به شماست با پشتیبانی تماس بگیرید."
                    request.POST["link"] = settings.PROJECT_DOMAIN
                    return general_error_page(request)
                
                promo = PromoCode.objects.get(pk=request.session["promo_code"].pk)
                promo.assigned_mail = request.session["giftinvoice"].metadata['giver_email']
                promo.save()
                promo.used = True
                request.session["promo_code"]=promo
                
            gateway = request.POST.get('gateway')

            from plans.views import invoice_checkout
            return invoice_checkout(request,gateway)
    except:
        import sys
        print sys.exc_info()
    raise PermissionDenied()


@token_required
def startpayment(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser and request.session.get("subscription",None):
            
            if "promo_code" in request.session:
                if request.session["promo_code"].assigned_mail and \
                request.session["promo_code"].assigned_mail != request.session["subscription"].email:
                    request.POST=request.POST.copy()
                    request.POST["error_msg"] = u"متاسفانه کاربری با ایمیل دیگر با این کد تخفیف اقدام به ثبت نام کرده است.<br/>اگر این کد تخفیف متعلق به شماست با پشتیبانی تماس بگیرید."
                    request.POST["link"] = settings.PROJECT_DOMAIN
                    return general_error_page(request)
                
                promo = PromoCode.objects.get(pk=request.session["promo_code"].pk)
                promo.assigned_mail = request.session["subscription"].email
                promo.save()
                promo.used=True
                request.session["promo_code"]=promo
                
            gateway = request.POST.get('gateway')
            request.session["user_id"] = request.POST.get("user_id")
            from plans.views import invoice_checkout
            return invoice_checkout(request,gateway)
    except:
        import sys
        print sys.exc_info()
    raise PermissionDenied()



def gift_finalize_payment(session,request=None):
    callback = session['callback']
    logger = logging.getLogger("Device Payment Result")
    try:
        if session['transaction'].successful_payment and str(session['transaction'].res_code) == "0":
            invoice = session['giftinvoice']
            if invoice.promo_code:
                invoice.promo_code.assigned_mail = invoice.metadata['giver_email']
                invoice.promo_code.used=True
                invoice.promo_code.save()
            invoice.full_clean()
            invoice.save()
            invoice.post_paid_actions()
            sales_reference_id = '-'
            if "payment" in session:
                session["payment"].invoice = invoice
                session["payment"].save()
                sales_reference_id = session['payment'].sale_reference_id
            transaction = session['transaction']
            transaction.hamkharid_object = invoice
            transaction.full_clean()
            transaction.save()
        
            promo_code = PromoCode.generate(1,"AUTO_GIFT_%s"%invoice.plan.label,invoice.metadata['giver_name'])[0]
            invoice.generated_promo_code = promo_code
            invoice.save()
            
            
            r = requests.post(callback['url'],data={'success':True,'plan_amount':invoice.plan_amount/10,'sales_reference_id':sales_reference_id,'invoice_id':invoice.pk,'promo_code':promo_code.code,'tokenback':callback['token'],'token':session.session_key})
            logger.info(r.text)
            js = r.json()
            if(js['success']):
    
                if "payment" in session:
                    session["payment"].user_id = invoice.metadata['giver_id']
                    session["payment"].save()
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
            return general_error_page(request)
        return HttpResponseRedirect(js['redirect'])
    except:
        import sys
        logger.info(sys.exc_info())
    return HttpResponse(u"خطا در ارسال اطلاعات به پذیرنده")


def finalizepayment(session,request=None):
    subscription = session['subscription']
    callback = session['callback']
    logger = logging.getLogger("Device Payment Result")
    try:
        if session['transaction'].successful_payment and str(session['transaction'].res_code) == "0":
            subscription.uuid = "Unverified"+str(int(time.time()))+subscription.email
            subscription.user_id = "reg-"+session.session_key
            subscription.full_clean()
            subscription.save()
            invoice = session['invoice']
            invoice.subscription=subscription
            if invoice.promo_code:
                invoice.promo_code.assigned_mail = subscription.email
                invoice.promo_code.used=True
                invoice.promo_code.save()
            invoice.full_clean()
            invoice.save()
            invoice.post_paid_actions()
            if "payment" in session:
                session["payment"].invoice = invoice
                session["payment"].save()
            transaction = session['transaction']
            transaction.hamkharid_object = invoice
            transaction.full_clean()
            transaction.save()
        
            
            r = requests.post(callback['url'],data={'success':True,'invoice_id':invoice.pk,'tokenback':callback['token'],'token':session.session_key})
            logger.info(r.text)
            js = r.json()
            if(js['success']):
                subscription.uuid = js['uuid']
                subscription.user_id = js['user_id']
                subscription.full_clean()
                subscription.save()
                
                if "payment" in session:
                    session["payment"].user_id = js["user_id"]
                    session["payment"].save()
                
                
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
            return general_error_page(request)
        return HttpResponseRedirect(js['redirect'])
    except:
        import sys
        logger.info(sys.exc_info())
    return HttpResponse(u"خطا در ارسال اطلاعات به پذیرنده")



@token_required
def alter_user(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        user_id = request.POST.get("user_id")
        email = request.POST.get("email")
        if email and user_id:
            try:
                for obj in Subscription.objects.filter(user_id=user_id):
                    obj.email = email
                    obj.save()
                for obj in BankPayment.objects.filter(user_id=user_id):
                    obj.user_mail = email
                    obj.save()
            except:
                return HttpResponseBadRequest(json.dumps({"error":True}))
        return HttpResponse(json.dumps({"success":True}))
    raise PermissionDenied()



#New API! Session-Based
@token_required
def begin_invoice_payment(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser:            
            invoice_id = request.POST.get('invoice_id')
            user_id = request.POST.get("user_id")
            invoice = get_object_or_404(Invoice,pk=int(invoice_id))
            if invoice.subscription.user_id != user_id:
                raise Http404
            if invoice.paid:
                raise Http404
            request.session['invoice'] = invoice
            request.session['subscription'] = invoice.subscription
            request.session['user_mail'] = invoice.subscription.email
            return HttpResponse(json.dumps({"token":request.session.session_key,'url' : invoice.payment_url["mellat"],
                                            'amount' : invoice.amount/10,
                                            'plan_amount' : invoice.plan_amount/10,
                                            'label' : invoice.plan.label}))
    except:
        import sys
        print sys.exc_info()
    return HttpResponseBadRequest(json.dumps({"error":True}))


#New API! Session-Based
@token_required
def invoice_payment(request):
    try:
        if request.user.is_authenticated() and request.user.is_superuser and 'invoice' in request.session and 'subscription' in request.session:            
            gateway = request.POST.get('gateway')
            
            user_id = request.POST.get("user_id")
            invoice = request.session['invoice']
            if invoice.subscription.user_id != user_id:
                raise Http404
            
            callback_url = request.POST.get("callback_url",None)
            if not user_id or not gateway or not callback_url:
                return HttpResponseBadRequest(json.dumps({"error":True}))
            request.session['callback'] = {'token' : '','url' : callback_url}
            request.session['user_id'] = user_id
            request.session['invoice_payment'] = True
            
            
            if "promo_code" in request.session:
                if request.session["promo_code"].assigned_mail and \
                request.session["promo_code"].assigned_mail != request.session["subscription"].email:
                    request.POST=request.POST.copy()
                    request.POST["error_msg"] = "متاسفانه کاربری با ایمیل دیگر با این کد تخفیف اقدام به ثبت نام کرده است.<br/>اگر این کد تخفیف متعلق به شماست با پشتیبانی تماس بگیرید."
                    request.POST["link"] = settings.PROJECT_DOMAIN
                    return general_error_page(request)
                
                promo = PromoCode.objects.get(pk=request.session["promo_code"].pk)
                promo.assigned_mail = request.session["subscription"].email
                promo.save()
                request.session["promo_code"]=promo
            
            
            
            from plans.views import invoice_checkout
            return invoice_checkout(request,gateway)
    except:
        import sys
        print sys.exc_info()
    return HttpResponseBadRequest(json.dumps({"error":True}))

def invoice_payment_back(session,request):
    subscription = session['subscription']
    callback = session['callback']
    logger = logging.getLogger("Invoice Payment Result")
    try:
        if session['transaction'].successful_payment and str(session['transaction'].res_code) == "0":
            invoice = session['invoice']
            if invoice.promo_code:
                invoice.promo_code.assigned_mail = invoice.subscription.email
                invoice.promo_code.used=True
                invoice.promo_code.save()
            invoice.full_clean()
            invoice.save()
            invoice.post_paid_actions()
            subscription.full_clean()
            subscription.save()
            if "payment" in session:
                session["payment"].invoice = invoice
                session["payment"].user_id = session["user_id"]
                session["payment"].save()
            transaction = session['transaction']
            transaction.hamkharid_object = invoice
            transaction.full_clean()
            transaction.save()
            analytics.track(session["user_id"],"successful_payment",{
                "invoice_id" : invoice.pk
            })
            analytics.track(session["user_id"],"subscription_renewal",{
                "latestPlan" : invoice.plan.label,
                "revenue": invoice.amount,
            })
            session.flush()
            return HttpResponseRedirect(callback['url'])
    except:
        import sys
        print sys.exc_info()
        import traceback
        print traceback.format_exc()
        logger.info(sys.exc_info())
    try:
        redirect = request.build_absolute_uri("/panel/invoicefail/%s"%session['transaction'].res_code)
        return HttpResponseRedirect(redirect)
    except:
        import sys
        logger.info(sys.exc_info())
        print sys.exc_info()
    return HttpResponse(u"خطا در ارسال اطلاعات به پذیرنده")


@token_required
def change_plan(request):
    if request.user.is_authenticated() and request.user.is_superuser and 'plan' in request.POST and 'device_id' in request.POST:
        plan = request.POST['plan']
        uuid = request.POST['device_id']
        plan = get_object_or_404(Plan,id=(int(plan)))
        subscription = get_object_or_404(Subscription,uuid=uuid)
        if subscription.active_invoice.paid:
            raise Http404()
        if subscription.plan.pk == plan.pk:
            return HttpResponse(json.dumps({"duplicate":True,'invoice_id':subscription.active_invoice.id}))    
        invoice = subscription.create_new_invoice(plan=plan)
        return HttpResponse(json.dumps({"success":True,'invoice_id':invoice.id}))        
    raise PermissionDenied()



@token_required
def block_device_switch(request):
    """Get a uuid and change related device status to BLOCKED and active it, if it is already BLOCKED.
    """
    if request.user.is_authenticated() and request.user.is_superuser:
        uuid = request.POST['device_id']
        subscription = get_object_or_404(Subscription, uuid=uuid)
        if subscription.status == 6:
            # Device is blocked, so activate it
            subscription.status = 2
        else:
            # Block device.
            subscription.status = 6
        subscription.save()
        return HttpResponse(json.dumps({"success":True,'uuid': uuid,'status': subscription.status}))
    raise PermissionDenied()


def general_error_page(request):
    data = request.POST.copy()
    data["general_page"] = True
    import plans.views
    return plans.views.api_create_redirect_page(request,data)


@token_required
def generate_promo_code(request):
    """Generate and return request base on request type
    """
    if request.user.is_authenticated() and request.user.is_superuser:
        req_type = request.POST.get('type', None)
        promo_partner = request.POST.get('partner', None)
        camp_name = request.POST.get('campaign', None)

        res = {}

        if req_type:
            setting_obj = Settings.objects.get(pk=1)
            if req_type == 'referred' and promo_partner:
                if setting_obj.REFERRED_GETS_PROMO:
                    promo_type = setting_obj.REFERRED_PROMO_TYPE
                    promo_obj = PromoCode.generate(1, promo_type, promo_partner)[0]
                    res['code'] = promo_obj.code
            elif req_type == 'campaign' and camp_name:
                campaign = setting_obj.CAMPAIGN_PROMO_TYPE
                partner = setting_obj.CAMPAIGN_PROMO_PARTNER
                if campaign and campaign.is_active() and camp_name.lower() == campaign.label.lower():
                    promo_obj = PromoCode.generate(1, campaign, partner)[0]
                    res['code'] = promo_obj.code

            if not res.get('code', None):
                res['error'] = 'Invlid request'
        else:
            res['error'] = 'Missing request fields'
        return HttpResponse(json.dumps(res))

    raise PermissionDenied()

@token_required
def reporter(request):
    if request.user.is_authenticated() and request.user.is_superuser:
        from_date = request.GET.get("from", None)
        to_date = request.GET.get("to", None)

        if not (from_date and to_date):
            return HttpResponse(json.dumps({'error': True}))

        from_date = parser.parse(from_date)
        to_date = parser.parse(to_date)

        renew_user = Invoice.objects.filter(pay_time__gte=from_date,
                                            pay_time__lte=to_date,
                                            subscription__created_at__lt=from_date)

        new_user = Invoice.objects.filter(pay_time__gte=from_date,
                                          pay_time__lte=to_date,
                                          subscription__created_at__gte=from_date)
        res = {
            "new_user": {
                "sum": new_user.count(),
                "items": []
            },
            "renew_user": {
                "sum": renew_user.count(),
                "items": []
            },
            "total": Subscription.objects.filter(status=2).count()  # Active subscriptions
        }

        for i in range(new_user.count()):
            obj = new_user[i]
            res["new_user"]["items"].append({"user": obj.subscription.email,
                                             "plan": obj.plan.label,
                                             "time": str(obj.pay_time)})

        for i in range(renew_user.count()):
            obj = renew_user[i]
            res["renew_user"]["items"].append({"user": obj.subscription.email,
                                               "plan": obj.plan.label,
                                               "time": str(obj.pay_time)})

        return HttpResponse(json.dumps(res))
    raise PermissionDenied()
