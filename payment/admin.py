from django.contrib import admin
from django import forms
import models
from .models import Settings


def radio_boolean(label):
    return forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((False, 'False'), (True, 'True')),
        widget=forms.RadioSelect,
        label=label
    )


class SettingsForm(forms.ModelForm):
    OMGPAY_DISABLE_FOR_USERS = radio_boolean('Disable payment gateway for users')
    REFERRED_GETS_PROMO = radio_boolean('Send promo code to referred users')
    USERS_GETS_PROMO = radio_boolean('Generate promo code based on user points on new invoice')
    class Meta:
        model = Settings
        fields = "__all__"


class SettingsAdmin(admin.ModelAdmin):
    form = SettingsForm

    fieldsets = (
        ("Friend invitation properties", {
            'fields': (('REFERRED_GETS_PROMO', 'REFERRED_PROMO_TYPE'),
                       ('USERS_GETS_PROMO'),),
            'classes': ('wide',)
        }),
        ('Campaign promo', {
            'fields':  ('CAMPAIGN_PROMO_PARTNER', 'CAMPAIGN_PROMO_TYPE'),
            'classes': ('wide',)
        }),
        ("Payment setup", {
            'fields': ('OMGPAY_DISABLE_FOR_USERS',),
            'classes': ('wide', 'collapse')
        }),
    )

    def has_add_permission(self, request):
        num_objects = self.model.objects.count()
        if num_objects >= 1:
            return False
        else:
            return True

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Settings, SettingsAdmin)
# import models


class ReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

class BankPaymentAdmin(ReadOnlyAdmin):
    list_display = ('user_mail', 'invoice_number', 'user_id', 'pay_time', 'gateway', 'ref_id')
    search_fields = ('user_mail',)
    list_filter = ('gateway',)


class BankTransactionAdmin(ReadOnlyAdmin):
    list_filter = ('successful_payment', )


admin.site.register(models.BankTransaction, BankTransactionAdmin)
admin.site.register(models.BankPayment, BankPaymentAdmin)
