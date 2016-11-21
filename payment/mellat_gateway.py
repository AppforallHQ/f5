import os
import suds.client
from .models import BankTransaction
from datetime import datetime
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
import time,binascii,random
import payment.views
from payment.models import BankPayment
import analytics
from django.conf import settings


TERMINAL_ID = settings.MELLAT_PAYMENT["TERMINAL_ID"]
USERNAME = settings.MELLAT_PAYMENT["USERNAME"]
PASSWORD = settings.MELLAT_PAYMENT["PASSWORD"]
ENDPOINT = "https://bpm.shaparak.ir/pgwchannel/services/pgw?wsdl"

CATASTROPHIC_ERRORS = [21,22,23,24,25,34,61,412,413,414,415,416,417,418,419,421]

def AmirId(data):
    return (int(time.time())<<32 | (binascii.crc32(data) & 0xfffffffc) | random.randint(0,3))


def checkout(request, invoiceDate, redirectAddress, bank_transaction,failredirectAddress):
    invoiceNumber = AmirId(request.session['user_mail'])
    amount = bank_transaction.amount
    request.session["invoice_id"] = invoiceNumber
    now = datetime.now()
    
    pay = BankPayment()
    pay.invoice_number = invoiceNumber
    pay.amount = amount
    pay.session_key = request.session.session_key
    pay.user_mail = request.session["user_mail"]
    pay.gateway="mellat"
    pay.user_id = request.session.get("user_id",None)
    pay.save()
    
    context = {'terminalId': TERMINAL_ID,
               'userName': USERNAME,
               'userPassword': PASSWORD,
               'orderId': invoiceNumber,
               'amount': amount,
               'localDate': now.strftime("%Y%m%d"),
               'localTime': now.strftime("%H%I%S"),
               'additionalData': pay.user_mail,
               'callBackUrl': redirectAddress,
               'payerId': "0"
               }

    print context

    client = suds.client.Client(ENDPOINT)
    result = client.service.bpPayRequest(**context).split(",")

    if result[0] !="0" and not os.environ.get('DEVELOPMENT', False):
        if int(result[0]) in CATASTROPHIC_ERRORS:
            analytics.identify("Pivot_Error",traits={
                'email': "REPORT_EMAIL"
            })
            analytics.track("Pivot_Error","f5_error",{
                "error" : result[0],
                "reference" : invoiceNumber,
            })
            analytics.flush()

        print result
        request.session['transaction'].res_code = int(result[0])
        pay.ref_id = result[0]
        pay.save()
        return payment.views.create_redirect_page(request,{"mellat":True,"error":True})
    print bank_transaction
    context["refId"] = result[1]
    pay.ref_id = context["refId"]
    pay.save()
    bank_transaction.ref_id = context["refId"]
    request.session['transaction']=bank_transaction
    context["mellat"]=True
    return payment.views.create_redirect_page(request,context)
    

def payment_result(session):
    #<QueryDict: {u'SaleReferenceId': [u''], u'SaleOrderId': [u'16'], u'RefId': [u'B578CAE5D558E08B'], u'ResCode': [u'17'], u'CardHolderInfo': [u'']}>
    #<QueryDict: {u'SaleReferenceId': [u'101945350442'], u'SaleOrderId': [u'22'], u'RefId': [u'5233605972DEF416'], u'ResCode': [u'0'], u'CardHolderInfo': [u'A10C10968086BD2FF2C410FB2173FBC850535DD8A342D8EDCD972A999243C729']}>
    '''
    Amir Test:
    RefId:E4AB6A9A880D9C4E
    ResCode:0
    SaleOrderId:6085916061981557226
    SaleReferenceId:104273365199
    CardHolderInfo:My Card Hash
    CardHolderPan: My Card Number
    '''
    if session.get("transaction",None) and session['transaction'].res_code != 0:
        return session.get('transaction',None)
    POST = session['post']
    
    session["payment"].res_code = POST[u"ResCode"]
    session["payment"].sale_reference_id = POST["SaleReferenceId"]
    session["payment"].save()
    
    
    withdrawal = session['transaction']
       
    if POST[u"ResCode"] != '0' or POST[u'RefId'] != withdrawal.ref_id:
        withdrawal.res_code = POST[u"ResCode"]
    else:
        session["payment"].payment_card = POST["CardHolderPan"]
        session["payment"].save()
        context = {'terminalId': TERMINAL_ID,
                   'userName': USERNAME,
                   'userPassword': PASSWORD,
                   'orderId': session['invoice_id'],
                   'saleOrderId': POST['SaleOrderId'],
                   'saleReferenceId': POST['SaleReferenceId'],
                   }

        client = suds.client.Client(ENDPOINT)

        verify_result = client.service.bpVerifyRequest(**context)
        if verify_result == "0":
          settle_result = client.service.bpSettleRequest(**context)
          if settle_result in ["0", "45"]:
            withdrawal.res_code = "0"
            session["payment"].res_code = "0"
            withdrawal.gateway_transaction_id = POST[u"SaleReferenceId"]
            withdrawal.successful_payment = True
          else:
            withdrawal.res_code = settle_result
            session["payment"].res_code = settle_result
            session["payment"].save()
        elif verify_result == "43": #Already Here!
            pass
        else:
          withdrawal.res_code = verify_result
          session["payment"].res_code = verify_result
          session["payment"].save()

    return withdrawal
