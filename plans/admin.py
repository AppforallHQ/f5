from django.contrib import admin
from payment.admin import ReadOnlyAdmin

from .models import Subscription, Plan, PromoCode, PromoType, PromoTypePlanDetail, InvitePromo

class PromoCodeAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('code', 'partner', 'promo_type', 'created_at', 'used', 'used_at')
    list_filter = ('promo_type', 'used', 'partner',)

class PromoTypePlanDetailAdmin(admin.ModelAdmin):
    list_display = ('promo_type', 'plan', 'final_price', 'discount')

class InvitePromoAdmin(ReadOnlyAdmin):
    search_fields = ('giver_email', 'getter_email')
    list_display = ('giver_name', 'giver_email', 'getter_name', 'getter_email')

class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('email', 'user_id', 'uuid')
    list_display = ('email', 'user_id', 'status', 'created_at', 'due_date')
    list_filter = ('status',)

admin.site.register(Plan)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(PromoType)
admin.site.register(PromoTypePlanDetail, PromoTypePlanDetailAdmin)
admin.site.register(InvitePromo, InvitePromoAdmin)
