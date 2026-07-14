from django import forms
from .models import Vehicle

class TailwindFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 rounded border-slate-700 text-blue-600 focus:ring-blue-500 bg-slate-900'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full rounded-lg border border-slate-700 bg-slate-900/50 px-4 py-2.5 text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors'
                })

class VehicleForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'registration_number', 'name', 'model', 'vehicle_type', 
            'max_load_capacity', 'current_odometer', 'acquisition_cost', 
            'purchase_date', 'status', 'image'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_registration_number(self):
        reg = self.cleaned_data.get('registration_number')
        if reg:
            reg = reg.strip().upper()
        return reg

    def clean_max_load_capacity(self):
        capacity = self.cleaned_data.get('max_load_capacity')
        if capacity and capacity <= 0:
            raise forms.ValidationError("Maximum load capacity must be greater than zero.")
        return capacity

    def clean_current_odometer(self):
        odometer = self.cleaned_data.get('current_odometer')
        if odometer is not None and odometer < 0:
            raise forms.ValidationError("Odometer value cannot be negative.")
        return odometer
