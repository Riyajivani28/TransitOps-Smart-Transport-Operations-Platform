from django import forms
from .models import Maintenance
from vehicles.models import Vehicle
from vehicles.forms import TailwindFormMixin

class MaintenanceForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ['vehicle', 'maintenance_type', 'description', 'start_date', 'end_date', 'cost', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude retired vehicles, but allow currently assigned vehicle in case of editing
        vehicle_qs = Vehicle.objects.exclude(status='Retired')
        if self.instance and self.instance.pk:
            vehicle_qs = vehicle_qs | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
        self.fields['vehicle'].queryset = vehicle_qs.distinct()

    def clean_cost(self):
        cost = self.cleaned_data.get('cost')
        if cost is not None and cost < 0:
            raise forms.ValidationError("Maintenance cost cannot be negative.")
        return cost
