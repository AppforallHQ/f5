from datetime import datetime
import os, httplib, logging, urllib, time

from OpenSSL import crypto

from .models import BankTransaction, WalletWithdrawal, WalletDeposit, Settings
from django.core.urlresolvers import reverse

from django.conf import settings

from django.shortcuts import render_to_response
from django.template.context import RequestContext

from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import redirect

import mellat_gateway
import plans.views

OMGPAY_MOCK_BANK_GATEWAY = getattr(settings, 'OMGPAY_MOCK_BANK_GATEWAY', False)
OMGPAY_DISABLE_FOR_USERS = Settings.objects.get(pk=1).OMGPAY_DISABLE_FOR_USERS

def checkout(request, redirectAddress, hamkharid_object, amount, gateway,failAddress):
    print settings.OMGPAY_ACTIVE_GATEWAYS
    if gateway not in settings.OMGPAY_ACTIVE_GATEWAYS:
        raise Http404
    
    if OMGPAY_DISABLE_FOR_USERS == True and amount != 0:
        raise Http404
    
    invoiceDate = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    if gateway == "wallet":
        transaction = WalletWithdrawal(wallet=request.user.wallet.get())
        checkout_handler = _checkout_via_wallet
    else:
        if OMGPAY_MOCK_BANK_GATEWAY == True or amount==0:
            transaction = BankTransaction()
            checkout_handler = mock_checkout
        elif gateway == "mellat":
            transaction = BankTransaction()
            checkout_handler = mellat_gateway.checkout

    transaction.hamkharid_object = hamkharid_object
    transaction.amount = amount
    transaction.res_code=0
    request.session['transaction'] = transaction

    return checkout_handler(request, invoiceDate, redirectAddress, transaction,failAddress)


def get_encrypted_session_token(request):    
    from Crypto.Cipher import AES
    import base64,hashlib
    BLOCK_SIZE = 32
    PADDING = ' '
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    cipher = AES.new(hashlib.sha256(settings.SECRET_KEY).digest(), AES.MODE_CBC, hashlib.md5("IV be zehnam naresid dasti ye chizi gozashtam! :D").digest())
    encoded = EncodeAES(cipher, request.session.session_key)
    return encoded


def retrieve_session_key(data):
    from Crypto.Cipher import AES
    import base64,hashlib
    BLOCK_SIZE = 32
    PADDING = ' '
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
    cipher = AES.new(hashlib.sha256(settings.SECRET_KEY).digest(), AES.MODE_CBC, hashlib.md5("IV be zehnam naresid dasti ye chizi gozashtam! :D").digest())
    decoded = DecodeAES(cipher, data)
    return decoded


def create_redirect_page(request,data):
    if not "general_page" in data:
        data['result_url'] = request.build_absolute_uri(reverse(plans.views.invoice_payment_result,kwargs={"gateway":"mellat"}))
        data['token'] = get_encrypted_session_token(request)
    data['uri'] = request.build_absolute_uri(settings.STATIC_URL)
    return render_to_response('payment.html', context_instance=RequestContext(request,data))


def mock_payment_result(session):
    withdrawal = session.get('transaction',None)
    withdrawal.successful_payment = True
    withdrawal.res_code = "0"
    session["transaction"] = withdrawal
    session.save()
    #withdrawal.full_clean()
    #withdrawal.save()
    return withdrawal

def mock_checkout(request, invoiceDate, redirectAddress, bank_transaction,failAddress):
    return create_redirect_page(request,{"mock":True})

def _checkout_via_passargad(request, invoiceDate, redirectAddress, bank_transaction,failAddress):
    MERCHANT_CODE = settings.PASARGAD_PAYMENT['MERCHANT_CODE']
    TERMINAL_CODE = settings.PASARGAD_PAYMENT['TERMINAL_CODE']
    PAY_ACTION = "1003"

    invoiceNumber = bank_transaction.pk
    amount = bank_transaction.amount

    timeStamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def __signature(data):
        key_path = os.path.dirname(os.path.abspath(__file__)) + '/server.key'
        server_key = open(key_path, 'r').read()
        rsa = crypto.load_privatekey(crypto.FILETYPE_PEM, server_key)
        return crypto.sign(rsa, data, 'sha1')

    data = "#".join(["", MERCHANT_CODE, TERMINAL_CODE, str(invoiceNumber),
        invoiceDate, str(amount), redirectAddress, PAY_ACTION, timeStamp, ""])
    signature = __signature(data)


    context = {'invoiceNumber': invoiceNumber,
               'invoiceDate': invoiceDate,
               'amount': amount*10, #In rials
               'terminalCode': TERMINAL_CODE,
               'merchantCode': MERCHANT_CODE,
               'redirectAddress': redirectAddress,
               'timeStamp': timeStamp,
               'action': PAY_ACTION,
               "result": signature.encode('base64'),
               }

    if OMGPAY_MOCK_BANK_GATEWAY == False:
        return render_to_response('payment.html', context,
                                  context_instance=RequestContext(request))
    else:
        from django.shortcuts import redirect
        response = redirect(redirectAddress)
        response["Location"] += "?id=%s" % invoiceNumber
        return response

def _checkout_via_wallet(request, invoiceDate, redirectAddress, wallet_withdrawal,failAddress):
    invoiceNumber = wallet_withdrawal.pk
    amount = wallet_withdrawal.amount

    user_wallet = request.user.wallet.get()
    resulting_balance = float(user_wallet.balance())-float(amount)
    if  resulting_balance >= 0 \
    and wallet_withdrawal.successful_payment == False:
        from django.shortcuts import redirect
        response = redirect(redirectAddress)
        response["Location"] += "?wallet_withdrawal_id=%s" % wallet_withdrawal.pk
        return response
    else:
        return render_to_response(
            'no_credit_in_wallet.html',
            {"amount_needed": int(-resulting_balance)},
            context_instance=RequestContext(request)
        )

def passargad_payment_result(request):
    httplib.HTTPConnection.debuglevel = 1

    values = {'invoiceUID': request.GET["tref"]}

    data = urllib.urlencode(values)
    cn = httplib.HTTPSConnection('epayment.bankpasargad.com', httplib.HTTPS_PORT)
    cn.putrequest('POST', '/CheckTransactionResult.aspx')
    cn.putheader('content-type', 'application/x-www-form-urlencoded')
    cn.putheader('content-length', len(data))
    cn.endheaders()
    cn.send(data)
    response = cn.getresponse().read().strip()
    logger.info(response)

    import xml.dom.minidom
    node = doc.getElementsByTagName("resultObj")[0]
    doc = xml.dom.minidom.parseString(response)

    def first_child_of(node, child_name):
        return node.getElementsByTagName(child_name)[0].firstChild.nodeValue

    result = first_child_of(node, "result")
    action = first_child_of(node, "action")
    ref_id = first_child_of(node, "transactionReferenceID")
    invoiceNumber = first_child_of(node, "invoiceNumber")
    merchantCode = first_child_of(node, "merchantCode")
    terminalCode = first_child_of(node, "terminalCode")


    withdrawal = BankTransaction.objects.get(pk=request.GET['id'])

    if result == 'True' \
    and merchantCode == MERCHANT_CODE \
    and terminalCode == TERMINAL_CODE \
    and action == PAY_ACTION:
        withdrawal.gateway_transaction_id = ref_id
        withdrawal.successful_payment = True

    return withdrawal

def payment_result(session, gateway):
    if (session.get('invoice',None) or session.get('giftinvoice',None)) and session.get('transaction',None):
        try:
            trans = session.get("transaction",None)
            if trans.amount==0:
                return mock_payment_result(session)
        except:
            pass
    
    if OMGPAY_DISABLE_FOR_USERS == True:
        raise Http404
    
    if OMGPAY_MOCK_BANK_GATEWAY == False:
        if gateway == "mellat":
            return mellat_gateway.payment_result(session)
        else:
            return passargad_payment_result(session)
    else:
        return mock_payment_result(session)


def wallet_deposit_checkout(request, wallet_deposit_id):
    wallet_deposit = WalletDeposit.objects.get(pk=wallet_deposit_id)
    redirectAddress = reverse(wallet_deposit_payment_result)
    amount = wallet_deposit.amount

    return checkout(request, redirectAddress, wallet_deposit, amount, from_wallet=False)

def wallet_deposit_payment_result(request):
    bank_transaction = payment_result(request)
    wallet_deposit = bank_transaction.hamkharid_object

    if wallet_deposit.wallet.user != request.user:
        raise Http404

    if bank_transaction.successful_payment == True:
        if wallet_deposit.successful_payment == False:
            wallet_deposit.successful_payment = True
            wallet_deposit.deposited_via = bank_transaction
            wallet_deposit.full_clean()
            wallet_deposit.save()
    else:
        return HttpResponseBadRequest("bank failed")

    context = {}

    return render_to_response('wallet-deposit-result.html', context,
        context_instance=RequestContext(request))
