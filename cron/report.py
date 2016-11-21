# -*- coding: utf-8 -*-
import os,sys
sys.path.append(os.getcwd())

import django
django.setup()

import requests
import plans
from plans.models import Invoice,Subscription,Plan,ItemInvoice,PromoType
from payment.models import BankPayment
from cron.models import CronLog
from django.conf import settings
import analytics
import time,json
import logging
from django.utils import timezone
from datetime import timedelta
import traceback
from requests.auth import HTTPBasicAuth
from django.db.models import Sum
from base64 import b64encode

ERROR = timedelta(minutes=30)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('F5 Report Job')



def on_error(error, items):
    logger.error("ERROR %s ON ANALYTICS" % error)
    logger.error("Items: %s" % items)

analytics.on_error = on_error

FROM_DATE = timezone.now()-timedelta(days=1)

TEST_TYPES = r'(test|compensation|friends)'

def get_invoice_data(dic):
    Q = Invoice.objects.all()
    for (key,value) in dic.items():
        Q = Q.filter(**{key:value})
    
    return Q



analytics.identify('USER',{
    'email' : 'EMAIL'
})


sall = get_invoice_data({'pay_time__gte':FROM_DATE,'subscription__created_at__gte':FROM_DATE})
rall = get_invoice_data({'pay_time__gte':FROM_DATE,'subscription__created_at__lt':FROM_DATE})
tall = get_invoice_data({'pay_time__gte':FROM_DATE})


gift = ItemInvoice.objects.filter(pay_time__gte=FROM_DATE)



def aggregate(q):
    return int(q.aggregate(Sum('amount'))['amount__sum'] or 0)/10


new_full = []
for i in range(1,4):
    new_full.append([])
    q = sall.filter(amount=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i))
    new_full[-1].append(q.count())
    new_full[-1].append(aggregate(q))
new_full.append([sum([x[0] for x in new_full]),sum([x[1] for x in new_full])])


renew_full = []
for i in range(1,4):
    renew_full.append([])
    q = rall.filter(amount=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i))
    renew_full[-1].append(q.count())
    renew_full[-1].append(aggregate(q))
renew_full.append([sum([x[0] for x in renew_full]),sum([x[1] for x in renew_full])])



new_off = []
for i in range(1,4):
    new_off.append([])
    q = sall.filter(amount__lt=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i)).filter(amount__gt=0)
    new_off[-1].append(q.count())
    new_off[-1].append(aggregate(q))
new_off.append([sum([x[0] for x in new_off]),sum([x[1] for x in new_off])])


renew_off = []
for i in range(1,4):
    renew_off.append([])
    q = rall.filter(amount__lt=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i)).filter(amount__gt=0)
    renew_off[-1].append(q.count())
    renew_off[-1].append(aggregate(q))
renew_off.append([sum([x[0] for x in renew_off]),sum([x[1] for x in renew_off])])

new_vip = []
for i in range(1,4):
    new_vip.append([])
    q = sall.filter(plan=Plan.objects.get(id=i)).filter(amount=0).filter(promo_code__promo_type__label__iregex = r'(friends)')
    new_vip[-1].append(q.count())
    new_vip[-1].append(aggregate(q))
new_vip.append([sum([x[0] for x in new_vip]),sum([x[1] for x in new_vip])])


qa = tall.filter(promo_code__promo_type__label__iregex = r'(qa)')
qa_l = [qa.count(),aggregate(qa)]

dev = tall.filter(promo_code__promo_type__label__iregex = r'(dev)')
dev_l = [dev.count(),aggregate(dev)]



renew_vip = []
for i in range(1,4):
    renew_vip.append([])
    q = rall.filter(plan=Plan.objects.get(id=i)).filter(amount=0).filter(promo_code__promo_type__label__iregex = r'(friends)')
    renew_vip[-1].append(q.count())
    renew_vip[-1].append(aggregate(q))
renew_vip.append([sum([x[0] for x in renew_vip]),sum([x[1] for x in renew_vip])])


campaigns = []
for promotype in PromoType.objects.filter(active=True).exclude(label__iregex=TEST_TYPES):
    cq = tall.filter(promo_code__promo_type = promotype)
    if cq.count() > 0:
        campaigns.append({
            'key' : promotype.label,
            'value' : cq.count(),
            'price' : "{:,.0f} تومان".format(aggregate(cq)),
        })




analytics.identify("Admin_",{"email" : "admin@PROJECT.ir"})
analytics.track("Admin_",'financial_report',{
    'tables' : [{
        'title' : 'گزارش های کلی',
        'report' : [
            {
                'key' : "فروش جدید",
                'value' : sall.count(),
                'price' : "{:,.0f} تومان".format(aggregate(sall))
            },
            {
                'key' : "تمدید اشتراک",
                'value' : rall.count(),
                'price' : "{:,.0f} تومان".format(aggregate(rall))
            },
            {
                'key' : "فروش کل",
                'value' : tall.count(),
                'price' : "{:,.0f} تومان".format(aggregate(tall))
            },
            {
                'key' : 'اپفورال را هدیه بدهید',
                'value' : gift.count(),
                'price' : "{:,.0f} تومان".format(aggregate(gift))
            }
        ]},
        {
        'title' : 'گزارش با جزییات',
        'report' : [
            {
                'key' : "فروش جدید با <b style='color:#F00'>قیمت اصلی</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : new_full[0][0],
                'price' : "{:,.0f} تومان".format(new_full[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : new_full[1][0],
                'price' : "{:,.0f} تومان".format(new_full[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : new_full[2][0],
                'price' : "{:,.0f} تومان".format(new_full[2][1])
            },
            {
                'key' : "کل",
                'value' : new_full[3][0],
                'price' : "{:,.0f} تومان".format(new_full[3][1])
            },
            
            
            {
                'key' : "تمدید اشتراک با <b style='color:#F00'>قیمت اصلی</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : renew_full[0][0],
                'price' : "{:,.0f} تومان".format(renew_full[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : renew_full[1][0],
                'price' : "{:,.0f} تومان".format(renew_full[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : renew_full[2][0],
                'price' : "{:,.0f} تومان".format(renew_full[2][1])
            },
            {
                'key' : "کل",
                'value' : renew_full[3][0],
                'price' : "{:,.0f} تومان".format(renew_full[3][1])
            },
            
            
            {
                'key' : "فروش جدید با <b style='color:#F00'>تخفیف</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : new_off[0][0],
                'price' : "{:,.0f} تومان".format(new_off[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : new_off[1][0],
                'price' : "{:,.0f} تومان".format(new_off[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : new_off[2][0],
                'price' : "{:,.0f} تومان".format(new_off[2][1])
            },
            {
                'key' : "کل",
                'value' : new_off[3][0],
                'price' : "{:,.0f} تومان".format(new_off[3][1])
            },
            
            
            {
                'key' : "تمدید اشتراک با <b style='color:#F00'>تخفیف</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : renew_off[0][0],
                'price' : "{:,.0f} تومان".format(renew_off[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : renew_off[1][0],
                'price' : "{:,.0f} تومان".format(renew_off[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : renew_off[2][0],
                'price' : "{:,.0f} تومان".format(renew_off[2][1])
            },
            {
                'key' : "کل",
                'value' : renew_off[3][0],
                'price' : "{:,.0f} تومان".format(renew_off[3][1])
            },
            
            
            {
                'key' : "اشتراک جدید <b style='color:#F00'>دوستان اپفورال</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : new_vip[0][0],
                'price' : "{:,.0f} تومان".format(new_vip[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : new_vip[1][0],
                'price' : "{:,.0f} تومان".format(new_vip[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : new_vip[2][0],
                'price' : "{:,.0f} تومان".format(new_vip[2][1])
            },
            {
                'key' : "کل",
                'value' : new_vip[3][0],
                'price' : "{:,.0f} تومان".format(new_vip[3][1])
            },
            
            
            {
                'key' : "تمدید اشتراک <b style='color:#F00'>دوستان اپفورال</b>",
                'value' : '',
                'price' : ''
            },
            {
                'key' : "۱ ماهه",
                'value' : renew_vip[0][0],
                'price' : "{:,.0f} تومان".format(renew_vip[0][1])
            },
            {
                'key' : "۳ ماهه",
                'value' : renew_vip[1][0],
                'price' : "{:,.0f} تومان".format(renew_vip[1][1])
            },
            {
                'key' : "۶ ماهه",
                'value' : renew_vip[2][0],
                'price' : "{:,.0f} تومان".format(renew_vip[2][1])
            },
            {
                'key' : "کل",
                'value' : renew_vip[3][0],
                'price' : "{:,.0f} تومان".format(renew_vip[3][1])
            },
            {
                'key' : "<b style='color:#F00'>تست تولید</b>",
                'value' : dev_l[0],
                'price' : "{:,.0f} تومان".format(dev_l[1])
            },
            {
                'key' : "<b style='color:#F00'>تست کنترل کیفیت</b>",
                'value' : qa_l[0],
                'price' : "{:,.0f} تومان".format(qa_l[1])
            },
        ]},
        {
        'title' : 'کمپین ها',
        'report' : campaigns
        },
    ]
})


analytics.flush()
