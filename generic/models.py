from django.db import models
from jsonfield import JSONField
from django.utils import timezone


def non_zero_validator(value):
    #This is just ridiculous
    #https://code.djangoproject.com/ticket/7609
    if value <= 0:
        raise ValidationError(u'%s is not a non-zero positive integer' % value)
    
def neg_validator(value):
    if value < 0:
        raise ValidationError(u"%s is negative" % value)


class GenericInvoice(models.Model):
    amount = models.IntegerField(validators=[neg_validator])
    original_amount = models.IntegerField(validators=[neg_validator])  #Price before discount
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)    
    pay_time = models.DateTimeField(null=True, blank=True)    
    invalid = models.BooleanField(default=False)
    ref_key = models.CharField(max_length=64,null=True, blank=True, default=None) # It is the reference key to a model outside
    metadata = JSONField(blank=True)

    @property
    def payment_url(self):
        res = {}

        for gateway in settings.OMGPAY_ACTIVE_GATEWAYS:
            kwargs = {
                #"invoice_pk": self.pk,
                "gateway": gateway
            }
            url = ''.join(["https://", Site.objects.get_current().domain,("/panel/pay/generic/%s" % (self.pk))])
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
    
