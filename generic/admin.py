import models

from django.contrib import admin
from payment.admin import ReadOnlyAdmin


class GenericInvoiceAdmin(ReadOnlyAdmin):
    list_display = ('amount', 'created_at', 'invalid', 'pay_time')
    list_filter = ('paid',)

admin.site.register(models.GenericInvoice, GenericInvoiceAdmin)
