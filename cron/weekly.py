# -*- coding: utf-8 -*-
import os,sys
sys.path.append(os.getcwd())

import django
django.setup()

import requests
import plans
from plans.models import Invoice,Subscription,Plan
from payment.models import BankPayment
from cron.models import CronLog
from django.conf import settings
import analytics
import time
import logging
from django.utils import timezone
from datetime import timedelta
import traceback
from requests.auth import HTTPBasicAuth
from django.db.models import Sum
from openpyxl import Workbook
from io import BytesIO
import base64

from customerio import CustomerIO
cio = CustomerIO(settings.CUSTOMER_SITE_ID, settings.CUSTOMER_API_KEY)



wb = Workbook(encoding='utf-8')
ws = wb.active
ws.title = "Financial Report"

analytics.identify("Admin_",{"email" : "EMAIL"})
time.sleep(1)



def get_invoice_data(dic):
    Q = Invoice.objects.all()
    for (key,value) in dic.items():
        Q = Q.filter(**{key:value})
    return Q

def get_extended_dic(query,date):
    return {
        query+'__year':date.year,
        query+'__month':date.month,
        query+'__day':date.day
    }

def aggregate(q):
    return int(q.aggregate(Sum('amount'))['amount__sum'] or 0)/10


analytics.identify('USER',{
    'email' : 'EMAIL'
})

lst = [
    'تاریخ',
    'تعداد کل فروش',
    'مبلغ کل فروش',
    'تعداد کل فروش اکانت یک ماهه',
    'تعداد کل فروش اکانت سه ماهه',
    'تعداد کل فروش اکانت شش ماهه',
    'تعداد کل فروش اکانت یک ماهه بدون تخفیف',
    'تعداد کل فروش اکانت سه ماهه بدون تخفیف',
    'تعداد کل فروش اکانت شش ماهه بدون تخفیف',
    'تعداد کل فروش اکانت یک ماهه با تخفیف',
    'تعداد کل فروش اکانت سه ماهه با تخفیف',
    'تعداد کل فروش اکانت شش ماهه با تخفیف',
    
    
    'مبلغ کل فروش اکانت یک ماهه',
    'مبلغ کل فروش اکانت سه ماهه',
    'مبلغ کل فروش اکانت شش ماهه',
    'مبلغ کل فروش اکانت یک ماهه بدون تخفیف',
    'مبلغ کل فروش اکانت سه ماهه بدون تخفیف',
    'مبلغ کل فروش اکانت شش ماهه بدون تخفیف',
    'مبلغ کل فروش اکانت یک ماهه با تخفیف',
    'مبلغ کل فروش اکانت سه ماهه با تخفیف',
    'مبلغ کل فروش اکانت شش ماهه با تخفیف',
    
    
    
    'تعداد دستگاه های تمدید شده',
    'مبلغ کل دستگاه های تمدید شده',
    'تعداد اکانت های VIP',
]
ws.append(lst)

RANGE = 90
FROM = (timezone.localtime(timezone.now())-timedelta(days=RANGE)).strftime("%Y/%m/%d")
TO = (timezone.localtime(timezone.now())-timedelta(days=1)).strftime("%Y/%m/%d")

if __name__ == '__main__':
    for i in range(RANGE,0,-1):
        FROM_DATE = timezone.localtime(timezone.now())-timedelta(days=i)
        res = []
        res.append(FROM_DATE.strftime("%Y/%m/%d"))
        
        rall = get_invoice_data(get_extended_dic('pay_time',FROM_DATE))
        rall = rall.filter(subscription__created_at__lt=(FROM_DATE-timedelta(3)))
        
        
        tall = get_invoice_data(get_extended_dic('pay_time',FROM_DATE))
        tall = tall.filter(amount__gt=0)
        
        frees = get_invoice_data(get_extended_dic('pay_time',FROM_DATE))

        frees = frees.filter(amount=0).exclude(promo_code__promo_type__label__iregex = r'(test)')
        frees_list = [29,30,31]
        for num in frees_list:
            frees = frees.exclude(promo_code__promo_type__id=num)
        
        res.append(tall.count() + frees.count())
        res.append(aggregate(tall))
        
        for i in range(1,4):
            q = tall.filter(plan=Plan.objects.get(id=i))
            res.append(q.count())
        
        for i in range(1,4):
            q = tall.filter(amount=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i))
            res.append(q.count())
            
        for i in range(1,4):
            q = tall.filter(amount__lt=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i)).filter(amount__gt=0)
            res.append(q.count())
        
        for i in range(1,4):
            q = tall.filter(plan=Plan.objects.get(id=i))
            res.append(aggregate(q))
        
        for i in range(1,4):
            q = tall.filter(amount=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i))
            res.append(aggregate(q))
            
        for i in range(1,4):
            q = tall.filter(amount__lt=Plan.objects.get(id=i).price).filter(plan=Plan.objects.get(id=i)).filter(amount__gt=0)
            res.append(aggregate(q))
        
        res.append(rall.count())
        res.append(aggregate(rall))
        
        res.append(frees.count())
        
        ws.append(res)

filename = '%s.xlsx'%(timezone.localtime(timezone.now()).strftime("%Y-%m-%d"))
wb.save('reports/'+filename)        
buf = BytesIO()
wb.save(buf)
buf.seek(0)
outp = base64.b64encode(buf.getvalue())

cio.track('Admin_','weekly_financial',from_date = FROM,to_date = TO,attachments = {filename : outp})

analytics.flush()

