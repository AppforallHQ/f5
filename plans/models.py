# -*- coding: utf-8 -*-

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from django.utils import timezone
from datetime import timedelta

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from django.core.mail import send_mail
from django.contrib.sites.models import Site

from django.core.urlresolvers import reverse
from jsonfield import JSONField

import requests
import json
import string
import random

import plans.signals

from django.conf import settings


class PercentField(models.IntegerField):
    """
    Float field that ensures field value is in the range 0-100.
    """
    default_validators = [
        MinValueValidator(0),
        MaxValueValidator(100),
    ]


# We use this hack currently so that we can use session-based registration
class _ForeignKey(models.ForeignKey):
    allow_unsaved_instance_assignment = True


def non_zero_validator(value):
    #This is just ridiculous
    #https://code.djangoproject.com/ticket/7609
    if value <= 0:
        raise ValidationError(u'%s is not a non-zero positive integer' % value)
    
def neg_validator(value):
    if value < 0:
        raise ValidationError(u"%s is negative" % value)

class Plan(models.Model):
    price = models.IntegerField(validators=[non_zero_validator])
    period_length = models.FloatField(validators=[non_zero_validator])
    overdue_length = models.FloatField()
    preinvoice_length = models.FloatField()
    invoice_expiration_length = models.IntegerField()
    interaction_endpoint_url = models.TextField(null=False)
    successful_payment_endpoint_url = models.TextField(null=False)
    fail_payment_endpoint_url = models.TextField(null=False)
    mail_endpoint_url = models.TextField(null=False)
    label = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.label


class PromoType(models.Model):
    label = models.CharField(max_length=128)
    active = models.BooleanField(default=True)
    expire_date = models.DateTimeField(null=True, blank=True,default=None)
    
    def is_active(self):
        if self.expire_date:
            return self.active and timezone.now() <= self.expire_date
        else:
            return self.active
    
    def __unicode__(self):
        return self.label

class PromoTypePlanDetail(models.Model):
    promo_type = models.ForeignKey("PromoType")
    plan = models.ForeignKey("Plan")
    final_price = models.IntegerField(null=True, blank=True)
    discount = PercentField(null=True, blank=True)

    class Meta:
        unique_together = ("promo_type", "plan")

    def clean(self):
        if self.final_price >= 0 and self.discount or \
           self.final_price is None and self.discount is None:
            raise ValidationError("One of two fields has to be filled (final_price, discount)")

    def __unicode__(self):
        return "%s: %s" % (self.promo_type, self.plan)

def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
            chars = chars.translate(None,'lio01')
            return ''.join(random.choice(chars) for _ in range(size))


class PromoCode(models.Model):
    code = models.CharField(max_length=128, unique=True)
    partner = models.CharField(max_length=128)
    used = models.BooleanField(default=False)
    promo_type = models.ForeignKey("PromoType")
    assigned_mail = models.CharField(max_length=256,blank=True,null=True,default=None)
    created_at = models.DateTimeField(null=True, blank=True,default=timezone.now)
    used_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        index_together = (('code'),)

    def __unicode__(self):
        return self.code

    @staticmethod
    def generate(num,label,partner):
        lst = []
        for i in range(num):
            created = False
            obj = None
            while not created:
                code = id_generator(6)
                obj,created = PromoCode.objects.get_or_create(
                    defaults=dict(
                        partner=partner,
                        used=False,
                        promo_type=PromoType.objects.get(label=label),
                    ),
                  code=code,
                )
            lst.append(obj)
        return lst
    
    def apply(self, invoice,commit=True):
        if self.used:
            raise ValidationError("USED", code='USED')
            
        if not self.promo_type.is_active():
            raise ValidationError("EXPIRED", code='EXPIRED')

        self.used = True
        try:
            plan_detail = self.promo_type.promotypeplandetail_set.get(plan=invoice.plan)
        except PromoTypePlanDetail.DoesNotExist:
            raise ValidationError("WRONG_PLAN", code='WRONG_PLAN', params={'plans': self.promo_type.promotypeplandetail_set.all().order_by('plan__label')})

        # Calculate final price based on plan_detail final_price or discount:
        if plan_detail.final_price >= 0:
            invoice.amount = plan_detail.final_price
        elif plan_detail.discount:
            discount = (invoice.amount/100) * plan_detail.discount
            invoice.amount = invoice.amount - discount

        # Set usage time
        self.used_at = timezone.now()

        invoice.promo_code = self
        if commit:
            self.save()
            invoice.save()



class Invoice(models.Model):
    amount = models.IntegerField(validators=[neg_validator])
    plan_amount = models.IntegerField(validators=[neg_validator])  #Added So that Prices can be changed in future
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    paid = models.BooleanField(default=False)
    subscription = _ForeignKey("Subscription")
    pay_time = models.DateTimeField(null=True, blank=True)
    expired = models.BooleanField(default=False)
    invalid = models.BooleanField(default=False)
    promo_code = models.ForeignKey("PromoCode", default=None, blank=True, null=True)
    plan = models.ForeignKey("Plan",null=True)


    def apply_promo_code(self, promo_code):
        promo_code = PromoCode.objects.get(code=promo_code)
        promo_code.apply(self,commit=False)

        return self.amount, promo_code

    @property
    def payment_url(self):
        res = {}

        for gateway in settings.OMGPAY_ACTIVE_GATEWAYS:
            kwargs = {
                "gateway": gateway
            }
            url = ''.join(["https://", Site.objects.get_current().domain,("/panel/pay/invoice/%s" % (self.pk))])
            res[gateway] = url

        return res

    @property
    def status(self):
        if self.invalid:
            return "invalid"
        if self.expired:
            return "expired"
        if self.pay_time:
            return "paid"
        else:
            return "active"

    def mark_as_expired(self):
        self.expired = True
        self.full_clean()
        self.save()

    def mark_as_invalid(self):
        self.invalid = True
        self.full_clean()
        self.save()

    def mark_as_paid(self):
        self.paid = True
        self.full_clean()
        self.save()

    def post_paid_actions(self):
        print self.subscription.status
        self.pay_time = timezone.now()
        if self.subscription.status in \
            [Subscription.ACTIVE, Subscription.PREINVOICE]:
            self.started_at = self.subscription.due_date
            self.subscription.due_date += \
                timedelta(days=self.plan.period_length)
            self.expires_at = self.subscription.due_date
            self.subscription.status = Subscription.ACTIVE

        elif self.subscription.status == Subscription.NEW:
            self.subscription.due_date = self.pay_time + timedelta(days=settings.DAYS_BEFORE_SUBSCRIPTION_START)
            self.subscription.status = Subscription.PAID_NOT_ACTIVE
        else:
            self.started_at = self.pay_time
            self.subscription.due_date = self.pay_time + \
                timedelta(days=self.plan.period_length)
            self.expires_at = self.subscription.due_date
            self.subscription.status = Subscription.ACTIVE

        self.subscription.full_clean()
        self.subscription.save()
        self.save()


@receiver(plans.signals.activate_subscription)
def call_activation_endpoint(sender, **kwargs):
    kwargs["subscription"].call_endpoint_url_for_activation()
    import actions

@receiver(pre_save, sender=Invoice)
def possibly_run_post_paid_actions(sender, instance, **kwargs):
    try:
        obj = Invoice.objects.get(pk=instance.pk)
    except Invoice.DoesNotExist:
        pass
    else:
        if obj.paid == False and instance.paid == True: # change from unpaid to paid
            if instance.status == "expired":
                raise ValidationError("cannot change payment status of expired invoice",
                    code="expired invoice. payment not allowed")

@receiver(post_save, sender=Invoice)
def send_email_notification(sender, instance, **kwargs):
    if kwargs["created"]:
        import actions

class Subscription(models.Model):

    class Meta:
        unique_together = (('uuid',),)

    NEW = 1
    ACTIVE = 2
    PREINVOICE = 3
    OVERDUE = 4
    DEACTIVE = 5
    BLOCKED = 6
    PAID_NOT_ACTIVE = 7
    STATUS = (
        (NEW, 'New'), (PAID_NOT_ACTIVE,'Paid But Not Active'), (ACTIVE, 'Active'), (PREINVOICE, 'Pre-Invoice'),
        (OVERDUE, 'Overdue'), (DEACTIVE, 'Deactive'), (BLOCKED, 'Blocked'),
    )

    status = models.IntegerField(choices=STATUS, default=NEW)
    #plan = models.ForeignKey(Plan)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    due_date = models.DateTimeField(blank=True, null=True)
    uuid = models.TextField()
    email = models.EmailField()
    user_id = models.CharField(max_length=64,null=True,default=None)


    def activate(self):
        if self.status != self.PAID_NOT_ACTIVE:
            return
        invoice = self.active_invoice
        invoice.started_at = min(timezone.now(),self.due_date)
        self.due_date = invoice.started_at + timedelta(days=invoice.plan.period_length)
        invoice.expires_at = self.due_date
        self.status = self.ACTIVE
        self.full_clean()
        self.save()
        invoice.save()
        

    def call_endpoint_url_for_activation(self):
        import plans.tasks

        return plans.tasks.activate_subscription.delay(self)

    def call_endpoint_url_for_deactivation(self):
        import plans.tasks

        return plans.tasks.deactivate_subscription.delay(self)

    def issue_pre_invoice(self):
        pre_invoice = self.create_new_invoice(plan=self.plan)

        self.status = self.PREINVOICE
        self.full_clean()
        self.save()

        return pre_invoice

    def is_active(self):
        if self.status == Subscription.BLOCKED:
            return False
        # Check if there is any available time for users plan
        return timezone.now() < self.due_date+timedelta(1)
    
    def mark_as_overdue(self):
        self.status = self.OVERDUE
        self.full_clean()
        self.save()

    def end_grace_time(self):
        if self.status != self.OVERDUE:
            raise ValidationError("Subscription is not overdue",
                code="subscription is not overdue")

        self.mark_as_deactivated()

    def mark_as_deactivated(self):
        self.status = self.DEACTIVE
        self.full_clean()
        self.save()

    @property
    def active_invoice(self):
        try:
            invoice = [f for f in self.invoice_set.all().order_by('-created_at')][0]
            print invoice.id
            return invoice
        except IndexError:
            return None

    @property
    def current_invoice(self):
        try:
            invoice = self.invoice_set.get(expires_at__gte=timezone.now(),
                                       created_at__lte=timezone.now())
            print len(self.invoice_set.filter(expires_at__gte=timezone.now(),
                                       created_at__lte=timezone.now()))
        except:
            invoice = None
        return invoice if invoice else self.active_invoice
    
    @property
    def plan(self):
        return self.current_invoice.plan

    def create_new_invoice(self,plan,commit=True):
        #if self.active_invoice == None or self.active_invoice.paid:
        created_at = timezone.now() + \
            timedelta(days=plan.invoice_expiration_length)

        invoice = Invoice(amount=plan.price,
                          created_at=created_at,
                          subscription=self,
                          plan=plan,
                          plan_amount=plan.price,
                          paid=False)
        if commit:
            invoice.full_clean()
            invoice.save()

        return invoice

@receiver(pre_save, sender=Subscription)
def check_if_possible_status_is_change_allowed(sender, instance, **kwargs):
    try:
        obj = Subscription.objects.get(pk=instance.pk)
    except Subscription.DoesNotExist:
        pass
    else:
        if obj.status != instance.status:
            the_dict = dict(Subscription.STATUS)
            allowed_transitions = [
                (Subscription.NEW, Subscription.PAID_NOT_ACTIVE),
                (Subscription.PAID_NOT_ACTIVE,Subscription.ACTIVE),
                (Subscription.ACTIVE, Subscription.PREINVOICE),
                (Subscription.DEACTIVE, Subscription.ACTIVE), #
                # TODO: remove this shit and change tests accordingly
                (Subscription.NEW, Subscription.DEACTIVE), #
                (Subscription.NEW, Subscription.PREINVOICE), #
                (Subscription.PREINVOICE, Subscription.OVERDUE), #
                (Subscription.NEW, Subscription.OVERDUE), #
                (Subscription.ACTIVE, Subscription.DEACTIVE), #
                (Subscription.PREINVOICE, Subscription.DEACTIVE), #
                (Subscription.OVERDUE, Subscription.DEACTIVE), #
                (Subscription.PREINVOICE, Subscription.ACTIVE), #
                (Subscription.OVERDUE, Subscription.ACTIVE), #
                # Allow all statuses to be able to block.
                (Subscription.NEW, Subscription.BLOCKED), #
                (Subscription.ACTIVE, Subscription.BLOCKED), #
                (Subscription.PREINVOICE, Subscription.BLOCKED), #
                (Subscription.OVERDUE, Subscription.BLOCKED), #
                (Subscription.DEACTIVE, Subscription.BLOCKED), #
                (Subscription.BLOCKED, Subscription.ACTIVE), #
            ]
            if (obj.status, instance.status) not in allowed_transitions:
                raise ValidationError("cannot change status from %s to %s" % (the_dict[obj.status], the_dict[instance.status]),
                    code="cannot change_status")

@receiver(plans.signals.deactivate_subscription)
def call_deactivation_endpoint(sender, **kwargs):
    pass#kwargs["subscription"].call_endpoint_url_for_deactivation()


@receiver(post_save, sender=Subscription)
def create_invoice_for_new_subscription(sender, **kwargs):
    pass

class ItemInvoice(models.Model):
    amount = models.IntegerField(validators=[neg_validator])
    plan_amount = models.IntegerField(validators=[neg_validator])  #Added So that Prices can be changed in future
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)    
    pay_time = models.DateTimeField(null=True, blank=True)    
    invalid = models.BooleanField(default=False)
    promo_code = models.ForeignKey("PromoCode", default=None, blank=True, null=True)
    
    generated_promo_code = models.ForeignKey("PromoCode", related_name = '+',default=None,null=True,blank=True)
    plan = models.ForeignKey("Plan",null=True)
    metadata = JSONField()
    
    
    def apply_promo_code(self, promo_code):
        promo_code = PromoCode.objects.get(code=promo_code)
        promo_code.apply(self,commit=False)

        return self.amount, promo_code

    @property
    def payment_url(self):
        res = {}

        for gateway in settings.OMGPAY_ACTIVE_GATEWAYS:
            kwargs = {
                #"invoice_pk": self.pk,
                "gateway": gateway
            }
            url = ''.join(["https://", Site.objects.get_current().domain,("/panel/pay/giftinvoice/%s" % (self.pk))])
            res[gateway] = url

        return res
    
    def post_paid_actions(self):
        self.pay_time = timezone.now()
        self.save()
        
    @property
    def status(self):
        if self.pay_time:
            return "paid"
        else:
            return "active"

class GetOrNoneManager(models.Manager):
    """Adds get_or_none method to objects
    """
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class InvitePromo(models.Model):
    getter_email = models.EmailField(max_length=254)
    getter_name = models.CharField(max_length=40, default="Anonymous")
    getter_promo = models.ForeignKey("PromoCode", related_name="getter_promo")
    giver_email = models.EmailField(max_length=254)
    giver_name = models.CharField(max_length=40, default="Anonymous")
    giver_promo = models.OneToOneField("PromoCode", related_name="giver_promo")

    objects = GetOrNoneManager()
