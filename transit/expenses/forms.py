from django import forms
from .models import Expense
from vehicles.models import Vehicle
from vehicles.forms import TailwindFormMixin

class ExpenseForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['vehicle', 'expense_type', 'amount', 'expense_date', 'remarks']
        widgets = {
            'expense_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude retired vehicles
        vehicle_qs = Vehicle.objects.exclude(status='Retired')
        if self.instance and self.instance.pk and self.instance.vehicle:
            vehicle_qs = vehicle_qs | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
        self.fields['vehicle'].queryset = vehicle_qs.distinct()
        self.fields['vehicle'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Expense amount must be greater than zero.")
        return amount
