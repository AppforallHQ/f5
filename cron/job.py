# -*- coding: utf-8 -*-
import os,sys
sys.path.append(os.getcwd())

import django
django.setup()

import requests
import plans
from plans.models import Invoimodels import PromoCode

from data import POINT_PROMO_STEPS


ERROR = timedelta(minutes=30)
SHADOW = 0
if "--shadow" in sys.argv:
    SHADOW = 1
logging.basicConfig(filename=("/var/log/f5/cron/job_%s.log"%time.time()),filemode='w',level=logging.INFO)
logger = logging.getLogger('F5 Cron Job')



def on_error(error, items):
    logger.error("ERROR %s ON ANALYTICS" % error)
    logger.error("Items: %s" % items)

analytics.on_error = on_error


def send_analytics(subscription, track, promo=None):
    logger.info("Analytics.Track : %s, Invoice : %s" %(track,subscription.active_invoice.payment_url['mellat']))
    
    if SHADOW:
        return
    track_data = {
        'latest_invoice_url' : subscription.active_invoice.payment_url['mellat'],
    }

    if promo:
        track_data['promo'] = promo

    analytics.track(subscription.user_id, track, track_data)


def issue_invoice_and_extra_day(subscription,cronlog):
    if SHADOW:
        logger.info("We have to Create Invoice and Give Extra Day to Device %s" % subscription.uuid)
        return
    subscription.due_date = timezone.now()
    subscription.issue_pre_invoice()
    cronlog = cronlog.mark_as_extra()
    send_analytics(subscription,cronlog.get_status())


def issue_new_invoice(subscription,cronlog):
    setting_obj = Settings.objects.get(pk=1)
    user_promo = get_promo(subscription.user_id) if setting_obj.USERS_GETS_PROMO else None

    if SHADOW:
        logger.info("We have to Create Invoice for Device %s. One Week Left!" % subscription.uuid)
        return
    subscription.issue_pre_invoice()
    cronlog = cronlog.mark_as_invite()
    send_analytics(subscription, cronlog.get_status(), promo=user_promo)


def issue_ending_notice(subscription, cronlog):
    if SHADOW:
        logger.info("We have to Notice End for Device %s. One Day Left!" % subscription.uuid)
        return
    cronlog = cronlog.mark_as_ending()
    send_analytics(subscription,cronlog.get_status())

def issue_extra_one_day(subscription,cronlog):
    if SHADOW:
        logger.info("We have to Give One Extra Day to Device %s." % subscription.uuid)
        return
    cronlog = cronlog.mark_as_extra()
    send_analytics(subscription,cronlog.get_status())


def block_device(subscription,cronlog):
    if SHADOW:
        logger.info("We have to Block Device %s" % subscription.uuid)
        return
    subscription.mark_as_overdue()
    cronlog = cronlog.mark_as_suspend()
    send_analytics(subscription,cronlog.get_status())
    requests.get("https://www.PROJECT.ir/panel/analytics/%s" % subscription.user_id,verify=False)


PAID = []
INVITE = []
ENDING = []
EXTRA = []
SUSPEND = []



try:
    for subscription in Subscription.objects.all():
        try:
            cronlog = CronLog.get_latest(subscription)
            if cronlog.is_blocked():
                continue
            if subscription.active_invoice.paid:
                if SHADOW:
                    if not cronlog.is_active():
                        logger.info("Subscription %s for user %s Must be Marked as Active" % (subscription.pk,subscription.email))
                        if len(CronLog.objects.filter(subscription=subscription))>1:
                            PAID .append(subscription)
                else:
                    if not cronlog.is_active():
                        logger.info("Subscription %s for user %s Marked as Active" % (subscription.pk,subscription.email))
                        if len(CronLog.objects.filter(subscription=subscription))>1:
                            PAID .append(subscription)
                        cronlog = cronlog.mark_as_active()

            if not subscription.due_date or (cronlog.is_active() and len([f for f in subscription.invoice_set.filter(paid=True)])<1):
                logger.warning("User with Email %s Was Not Paid! Maybe He's Not Registered :)" % subscription.email)
                if not SHADOW:
                    cronlog = cronlog.mark_as_blocked()
                    subscription.user_id="Not_Registered"
                    subscription.save()
                continue
            
            if subscription.status == subscription.PAID_NOT_ACTIVE and timezone.now() >= subscription.due_date-ERROR:
                logger.info("Activated Subscription %d" % subscription.id)
                subscription.activate()
            
            
            #Special Case... Due Date Passed and Nothing Issued
            if cronlog.is_active() and timezone.now() >= subscription.due_date-ERROR:
                logger.warning("User With Email %s Had an Unpaid Device" % subscription.email)
                subscription.invoice_set.filter(paid=False).delete()
                issue_invoice_and_extra_day(subscription,cronlog)
                EXTRA.append(subscription)
                continue
            
            
            if cronlog.is_active() and subscription.active_invoice.paid and \
                            timezone.now()+timedelta(7) >= subscription.due_date-ERROR:
                issue_new_invoice(subscription,cronlog)
                INVITE.append(subscription)
            
            elif cronlog.is_invite() and not subscription.active_invoice.paid and \
                            timezone.now()+timedelta(1) >= subscription.due_date-ERROR:
                issue_ending_notice(subscription,cronlog)
                ENDING.append(subscription)
                
            elif cronlog.is_noticed() and not subscription.active_invoice.paid and \
                            timezone.now() >= subscription.due_date-ERROR:
                issue_extra_one_day(subscription,cronlog)
                EXTRA.append(subscription)
            
            elif cronlog.is_extra() and not subscription.active_invoice.paid and \
                            timezone.now() >= subscription.due_date+timedelta(1)-ERROR:
                block_device(subscription,cronlog)
                SUSPEND.append(subscription)
            
            
        except Exception as e:
            logger.error("Error On Subscription With ID : %s" % subscription.pk)
            logger.error("Error: %s" % traceback.format_exc())
            
except Exception as e:
    import sys
    logger.error("Unhandled Exception %s" % e)
    
    
logger.info("Finished Running...")
logger.info("%d Users Paid Their Invoices" % len(PAID))
logger.info("Generated Invoice for %d Users" % len(INVITE))
logger.info("Noticed %d Users On Their Tomorrow Due Date" % len(ENDING))
logger.info("Gave %d Users an Extra One-Day Time" % len(EXTRA))
logger.info("Blocked %d Users" % len(SUSPEND))

if not SHADOW:
    analytics.identify("PROJECT_f5_report",{"email":"REPORT_EMAIL_ADDRESS"})
    analytics.track("PROJECT_f5_report","f5_cron_job_report",{
        "paid_invoice" : [{'id':str(t.pk),'email':t.email} for t in PAID],
        "unpaid_invoice_issued" : [{'id':str(t.pk),'email':t.email} for t in INVITE],
        "plan_ending_notice" : [{'id':str(t.pk),'email':t.email} for t in ENDING],
        "extra_day_notice" : [{'id':str(t.pk),'email':t.email} for t in EXTRA],
        "suspend_idevice" : [{'id':str(t.pk),'email':t.email} for t in SUSPEND],
    })

    analytics.flush()
