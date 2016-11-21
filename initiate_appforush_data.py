from django.conf import settings
from django.db import DEFAULT_DB_ALIAS as database
from django.contrib.auth.models import User
from django.conf import settings
from payment.models import Settings
import django
django.setup()

from plans.models import Plan,PromoCode,PromoType,PromoTypePlanDetail

import os
from django.contrib.sites.models import Site

new_domain = settings.PROJECT_DOMAIN

if User.objects.filter(username="admin").exists():
    print "Admin user already exists"
else:
    User.objects.db_manager(database).create_superuser('admin', 'joe@rubako.us', 'password')

if Settings.objects.filter(pk=1).exists():
    print "Settings object already exists"
else:
	s = Settings()
	s.OMGPAY_DISABLE_FOR_USERS = False
	s.save()

interaction_url = u'http://' + new_domain + '/panel/update_credit/%(uuid)s'
mail_endpoint_url = u'http://' + new_domain + '/panel/update_credit/%(uuid)s'
successful_payment_endpoint_url = u'http://' + new_domain + '/panel/invoice/%s'
fail_payment_endpoint_url = u'http://' + new_domain + '/panel/invoicefail/%s/%s'

plans = [[3, 30, 3, 150000], [3, 30*3, 3, 400000], [3, 30*6, 3, 600000]]


for plan_id, (overdue_length, period_length, preinvoice_length, price) in enumerate(plans, 1):
    plan = {'id': plan_id,
            'interaction_endpoint_url': interaction_url,
            'invoice_expiration_length': period_length,
            'mail_endpoint_url': mail_endpoint_url,
            'overdue_length': overdue_length,
            'period_length': period_length,
            'price': price,
            'preinvoice_length': preinvoice_length,
            'successful_payment_endpoint_url': successful_payment_endpoint_url,
            'fail_payment_endpoint_url': fail_payment_endpoint_url,
            'label': period_length/30
           }

    print "Creating plan %d" % plan["id"]
    plan_obj, created = Plan.objects.get_or_create(id=plan["id"], defaults=plan)

    if not created:
        plan.pop('price',None)
        print "... plan already existed. updating"
        Plan.objects.filter(pk=plan["id"]).update(**plan)


print "Updating default site"

current_site = Site.objects.get_current()
old_domain = current_site.domain
current_site.domain = new_domain
current_site.save()

print "... domain changed from %s to %s" % (old_domain, new_domain)


print "Creating Gift PromoCode Details..."

for plan in Plan.objects.all():
	promo_type,create = PromoType.objects.get_or_create(label = ("AUTO_GIFT_%s" % plan.label))
	det,create = PromoTypePlanDetail.objects.get_or_create(promo_type=promo_type,plan=plan,final_price=0)

print "Done."

