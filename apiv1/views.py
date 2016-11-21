# from django.contrib.auth.models import User, Group
from rest_framework import viewsets, mixins
from apiv1.serializers import SubscriptionSerializer, PlanSerializer, InvoiceSerializer,SettingsSerializer
from apiv1.serializers import BankPaymentSerializer
from plans.models import Subscription, Plan, Invoice
from payment.models import BankPayment,Settings


class SubscriptionViewSet(viewsets.ModelViewSet, mixins.CreateModelMixin):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filter_fields = ('uuid', 'email') 

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_fields = ('id',)

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    filter_fields = ('id',)

class BankPaymentViewSet(viewsets.ModelViewSet):
    queryset = BankPayment.objects.filter(invoice_object_content_type__model='invoice')
    serializer_class = BankPaymentSerializer
    filter_fields = ('user_id','invoice_object_id')

class SettingsViewSet(viewsets.ModelViewSet):
    queryset = Settings.objects.filter(pk=1)
    serializer_class = SettingsSerializer    

