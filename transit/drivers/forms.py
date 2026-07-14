from django import forms
from .models import Driver
from vehicles.forms import TailwindFormMixin

class DriverForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'name', 'photo', 'license_number', 'license_category', 
            'license_expiry_date', 'phone', 'email', 'safety_score', 
            'address', 'emergency_contact', 'status'
        ]
        widgets = {
            'license_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_safety_score(self):
        score = self.cleaned_data.get('safety_score')
        if score is not None and (score < 0 or score > 100):
            raise forms.ValidationError("Safety score must be between 0 and 100.")
        return score
