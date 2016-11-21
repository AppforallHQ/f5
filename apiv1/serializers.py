# from django.contrib.auth.models import User, Group
from rest_framework import serializers
from plans.models import Subscription, Plan, Invoice
from payment.models import BankPayment,Settings
from datetime import timedelta
from django.core import serializers as jsonserializer


class PlanSerializer(serializers.ModelSerializer):

    price = serializers.SerializerMethodField()
    def get_price(self,obj):
        return obj.price/10
    class Meta:
        model = Plan
        fields = ('id', 'overdue_length', 'price', 'period_length', 'label')
        
        
class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ('OMGPAY_DISABLE_FOR_USERS',)


class SubscriptionSerializer(serializers.ModelSerializer):

    active_invoice_payment_url = serializers.SerializerMethodField()
    active_invoice_id = serializers.SerializerMethodField()
    plan_label = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField('is_sub_active')
    plan = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ('status', 'due_date', 'plan', 'plan_label', 'uuid', 'email', 'active_invoice_payment_url', 'active_invoice_id', 'is_active')
    
    
    def get_plan(self,obj):
        if obj.plan:
            return obj.plan.pk
        else:
            return None
    
    def is_sub_active(self,obj):
        try:
            return obj.is_active()
        except:
            return False
    
    def get_active_invoice_payment_url(self, obj):
        return self.get_or_create_active_invoice(obj).payment_url
    
    def get_status(self,obj):
        print self.context['request'].GET.items()
        if str(self.context['request'].GET.get('activate',False)).lower() == "true":
            obj.activate()
        return obj.status
    
    def get_plan_label(self, obj):
        if obj.plan:
            return obj.plan.label
        else:
            return None

    def get_active_invoice_id(self, obj):
        return self.get_or_create_active_invoice(obj).pk

    def get_or_create_active_invoice(self, obj):
        active_invoice = obj.active_invoice
        if active_invoice == None:
            active_invoice = obj.create_new_invoice()

        return active_invoice

class InvoiceSerializer(serializers.ModelSerializer):

    subscription = serializers.SerializerMethodField()

    invoice_payment_url = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    plan_label = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    plan_amount = serializers.SerializerMethodField()
    
    
    def get_amount(self,obj):
        return obj.amount/10
    
    def get_plan_amount(self,obj):
        return obj.plan_amount/10
    
    def get_plan(self, obj):
        try:
            return obj.plan.pk
        except:
            return None
    
    def get_created_at(self,obj):
        return obj.created_at
    
    def get_invoice_payment_url(self, obj):
        return obj.payment_url

    def get_subscription(self, obj):
        try:
            return {"uuid": obj.subscription.uuid, "plan": obj.subscription.plan.pk, "plan_label": obj.subscription.plan.label}
        except:
            return {}
    
    def get_plan_label(self,obj):
        try:
            return obj.plan.label
        except:
            return ""
    
    class Meta:
        model = Invoice
        fields = ('id', 'plan', 'promo_code', 'plan_amount', 'status', 'amount', 'expires_at', 'paid',
            'subscription', 'pay_time', 'created_at', 'expired', 'invalid', 'invoice_payment_url','plan_label')


class BankPaymentSerializer(serializers.ModelSerializer):

    device_id = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField('get_invoice_id')
    amount = serializers.SerializerMethodField()
    
    def get_amount(self,obj):
        return obj.amount/10
    
    class Meta:
        model = BankPayment
        fields = ('user_id', 'pay_time', 'gateway', 'user_mail',
                  'amount', 'device_id', 'sale_reference_id', 'invoice')

    def get_device_id(self, obj):
        if obj.invoice and obj.invoice.subscription:
            return obj.invoice.subscription.uuid
        return None
    def get_invoice_id(self,obj):
        if obj.invoice:
            return obj.invoice.pk
        return None



