from django import forms
from .models import Trip
from vehicles.models import Vehicle
from drivers.models import Driver
from vehicles.forms import TailwindFormMixin
import uuid
from django.utils import timezone

class TripForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'trip_number', 'source', 'destination', 'vehicle', 'driver', 
            'cargo_weight', 'expected_distance', 'start_date', 'end_date', 
            'status', 'notes'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup datetime fields correctly for HTML input
        if self.instance and self.instance.start_date:
            self.initial['start_date'] = self.instance.start_date.strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.end_date:
            self.initial['end_date'] = self.instance.end_date.strftime('%Y-%m-%dT%H:%M')

        # Limit choices to available or currently assigned vehicles/drivers
        vehicle_qs = Vehicle.objects.filter(status='Available')
        driver_qs = Driver.objects.filter(status='Available')

        if self.instance and self.instance.pk:
            vehicle_qs = vehicle_qs | Vehicle.objects.filter(pk=self.instance.vehicle.pk)
            driver_qs = driver_qs | Driver.objects.filter(pk=self.instance.driver.pk)

        self.fields['vehicle'].queryset = vehicle_qs.distinct()
        self.fields['driver'].queryset = driver_qs.distinct()

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        driver = cleaned_data.get('driver')
        cargo_weight = cleaned_data.get('cargo_weight')
        status = cleaned_data.get('status')

        # 1. Vehicle Checks
        if vehicle:
            if vehicle.status == 'Retired':
                self.add_error('vehicle', "Retired vehicles cannot be assigned.")
            if vehicle.status == 'In Shop':
                self.add_error('vehicle', "Vehicles currently in maintenance (In Shop) cannot be assigned.")
            # If changing vehicle or creating new, ensure the new vehicle is not already on another trip
            if vehicle.status == 'On Trip' and (not self.instance.pk or self.instance.vehicle != vehicle):
                self.add_error('vehicle', "This vehicle is already assigned to another active trip.")

            # Cargo Weight Capacity Check
            if cargo_weight and vehicle.max_load_capacity < cargo_weight:
                self.add_error('cargo_weight', f"Cargo weight ({cargo_weight} kg) exceeds vehicle capacity ({vehicle.max_load_capacity} kg).")

        # 2. Driver Checks
        if driver:
            if driver.status == 'Suspended':
                self.add_error('driver', "Suspended drivers cannot be assigned.")
            if driver.is_license_expired:
                self.add_error('driver', "Drivers with expired licenses cannot be assigned.")
            # If changing driver or creating new, ensure the new driver is not already on another trip
            if driver.status == 'On Trip' and (not self.instance.pk or self.instance.driver != driver):
                self.add_error('driver', "This driver is already assigned to another active trip.")

        return cleaned_data


class DispatcherTripForm(forms.Form):
    """Simplified form used only by the Dispatcher Dashboard create-trip flow.
    Only exposes the 5 fields the dispatcher needs; everything else is auto-set.
    """
    source = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-4 py-3 text-sm text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all',
            'placeholder': 'e.g. Mumbai',
            'autocomplete': 'off',
            'id': 'id_d_source',
        })
    )
    destination = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-4 py-3 text-sm text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all',
            'placeholder': 'e.g. Pune',
            'autocomplete': 'off',
            'id': 'id_d_destination',
        })
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        empty_label='-- Select Available Vehicle --',
        widget=forms.Select(attrs={
            'class': 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-4 py-3 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all',
            'id': 'id_d_vehicle',
        })
    )
    driver = forms.ModelChoiceField(
        queryset=Driver.objects.none(),
        empty_label='-- Select Available Driver --',
        widget=forms.Select(attrs={
            'class': 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-4 py-3 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all',
            'id': 'id_d_driver',
        })
    )
    cargo_weight = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-4 py-3 text-sm text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all',
            'placeholder': 'e.g. 1500',
            'step': '0.01',
            'min': '0',
            'id': 'id_d_cargo_weight',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='Available')
        self.fields['driver'].queryset = Driver.objects.filter(status='Available')

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        driver = cleaned_data.get('driver')
        cargo_weight = cleaned_data.get('cargo_weight')

        if vehicle:
            if vehicle.status != 'Available':
                self.add_error('vehicle', f'Vehicle is not available (Status: {vehicle.status}).')
            elif cargo_weight and vehicle.max_load_capacity < cargo_weight:
                self.add_error('cargo_weight',
                    f'Cargo weight ({cargo_weight} kg) exceeds vehicle max capacity ({vehicle.max_load_capacity} kg).')

        if driver:
            if driver.status != 'Available':
                self.add_error('driver', f'Driver is not available (Status: {driver.status}).')
            if driver.is_license_expired:
                self.add_error('driver', 'This driver\'s license is expired.')

        return cleaned_data
