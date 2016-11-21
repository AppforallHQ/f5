from django.forms import ModelForm, ValidationError
from .models import Plan, Invoice

class PlanForm(ModelForm):

    class Meta:
        model = Plan

    def clean(self):
        #https://docs.djangoproject.com/en/dev/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
        cleaned_data = super(PlanForm, self).clean()
        overdue_length = cleaned_data.get("overdue_length")
        period_length = cleaned_data.get("period_length")

        if overdue_length and period_length and overdue_length >= period_length:
            msg = u"Overdue_length should be smaller than period_length."
            self._errors["overdue_length"] = self.error_class([msg])
            self._errors["period_length"] = self.error_class([msg])

            del cleaned_data["overdue_length"]
            del cleaned_data["period_length"]

        return cleaned_data

class InvoiceForm(ModelForm):

    class Meta:
        model = Invoice
