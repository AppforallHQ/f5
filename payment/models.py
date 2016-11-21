# -*- coding: utf-8 -*-
from django.utils import timezone

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import User

from django.db.models import Sum
from plans.models import Invoice, PromoType


def validate_only_one_instance(obj):
    model = obj.__class__
    if model.objects.count() > 0 and obj.id != model.objects.get().id:
        raise ValidationError("You can only create one {} instance".formate(model.__name__))


class Settings(models.Model):
    OMGPAY_DISABLE_FOR_USERS = models.BooleanField(default=False,verbose_name = "Disable payment gateway for users")

    USERS_GETS_PROMO = models.BooleanField(default=False)
    REFERRED_GETS_PROMO = models.BooleanField(default=False)
    REFERRED_PROMO_TYPE = models.ForeignKey(PromoType, null=True, blank=True,
                                            related_name='Referred')

    CAMPAIGN_PROMO_TYPE = models.ForeignKey(PromoType, null=True, blank=True,
                                            related_name='Campaign'
                                            , verbose_name='Current campaign promo type')
    CAMPAIGN_PROMO_PARTNER = models.CharField(max_length=50, default='کمپین‌های ویژه',
                                              verbose_name="Campaign promo partner")
    class Meta:
        verbose_name_plural = "Settings"
    def clean(self):
        validate_only_one_instance(self)
    
    def __str__(self):
        return "Current Settings"
    

#We use this hack currently so that we can use session-based registration
class _ForeignKey(models.ForeignKey):
    allow_unsaved_instance_assignment = True
    
class _GenericForeignKey(fields.GenericForeignKey):
    allow_unsaved_instance_assignment = True


class Wallet(models.Model):
    user = models.ForeignKey(User, related_name="wallet")
    def balance(self, before=None):
        if before == None:
            before = timezone.now()
        sum_of = lambda x: \
            x.objects.filter(
                wallet=self,
                successful_payment=True,
                date_created__lte=before
            ).aggregate(Sum("amount"))["amount__sum"] or 0

        withdrawal = sum_of(WalletWithdrawal)
        deposit = sum_of(WalletDeposit)

        return deposit - withdrawal

class Transaction(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=20,
                                 validators=[MinValueValidator(0)],
                                 editable=False)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    successful_payment = models.BooleanField(default=False)

class WithdrawalTransaction(Transaction):
    hamkharid_object_content_type = models.ForeignKey(ContentType)
    hamkharid_object_id = models.PositiveIntegerField()
    hamkharid_object = _GenericForeignKey(
        'hamkharid_object_content_type',
        'hamkharid_object_id'
    )


class BankTransaction(WithdrawalTransaction):
    gateway_transaction_id = models.CharField(
        max_length = 30,
        blank = True,
        editable = False
    )
    ref_id = models.CharField(max_length = 30,blank = True)
    res_code = models.CharField(max_length = 10,default = "-1")
    def __unicode__(self):
        return u"تراکنش بانکی %s" % self.gateway_transaction_id

class WalletTransaction(Transaction):
    wallet = models.ForeignKey(Wallet, editable=False)

    @property
    def balance(self):
        res = self.wallet.balance(before=self.date_created)
        return res

    @property
    def description(self):
        #POLYMORPHISM HACK
        try:
            return u"افزایش اعتبار بواسطه‌ی %s" % self.walletdeposit.deposited_via
        except WalletDeposit.DoesNotExist:
            pass

        try:
            return u"کاهش اعتبار بواسطه‌ی %s" % self.walletwithdrawal.hamkharid_object
        except WalletDeposit.DoesNotExist:
            pass

        return u"نامشخص"

class WalletWithdrawal(WalletTransaction):
    pass

class DepositTransaction(Transaction):
    pass

class WalletDeposit(DepositTransaction):
    deposited_via_content_type = models.ForeignKey(ContentType, blank=True, null=True)
    deposited_via_id = models.PositiveIntegerField(blank=True, null=True)
    deposited_via = _GenericForeignKey(
        'deposited_via_content_type',
        'deposited_via_id'
    )


class BankPayment(models.Model):
    user_id = models.CharField(max_length=64,null=True,default=None)
    pay_time = models.DateTimeField(auto_now_add=True, editable=False)
    gateway = models.CharField(max_length = 32)
    invoice_number = models.CharField(max_length = 32)
    user_mail = models.CharField(max_length = 256)
    session_key = models.CharField(max_length = 64)
    amount = models.PositiveIntegerField()
    ref_id = models.CharField(max_length = 64)
    res_code = res_code = models.CharField(max_length = 10,default = "-1")
    payment_card = models.CharField(max_length = 32)
    sale_reference_id = models.CharField(max_length = 32)
    #invoice = models.ForeignKey(Invoice,null=True,default=None)
    
    invoice_object_content_type = models.ForeignKey(ContentType, blank=True, null=True)
    invoice_object_id = models.PositiveIntegerField(blank=True, null=True)
    invoice = _GenericForeignKey(
        'invoice_object_content_type',
        'invoice_object_id'
    )
    
    
    reversal = models.BooleanField(default=False)
    class Meta:
        unique_together = (('gateway','invoice_number',))
        index_together = (('gateway','invoice_number'),('session_key',),('user_id',))

