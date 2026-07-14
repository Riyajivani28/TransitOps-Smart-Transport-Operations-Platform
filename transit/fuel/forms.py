from django import forms
from .models import FuelLog
from vehicles.models import Vehicle
from trips.models import Trip
from vehicles.forms import TailwindFormMixin

class FuelLogForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['vehicle', 'trip', 'fuel_date', 'liters', 'cost', 'fuel_station', 'notes']
        widgets = {
            'fuel_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude retired vehicles
        vehicle_qs = Vehicle.objects.exclude(status='Retired')
        if self.instance and self.instance.pk:
            vehicle_qs = vehicle_qs | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
        self.fields['vehicle'].queryset = vehicle_qs.distinct()
        
        # Trips can be linked
        self.fields['trip'].queryset = Trip.objects.all().order_by('-start_date')

    def clean_liters(self):
        liters = self.cleaned_data.get('liters')
        if liters is not None and liters <= 0:
            raise forms.ValidationError("Liters must be greater than zero.")
        return liters

    def clean_cost(self):
        cost = self.cleaned_data.get('cost')
        if cost is not None and cost <= 0:
            raise forms.ValidationError("Cost must be greater than zero.")
        return cost
