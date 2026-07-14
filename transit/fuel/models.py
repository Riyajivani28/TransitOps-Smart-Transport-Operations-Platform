from django.db import models
from vehicles.models import Vehicle
from trips.models import Trip

class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, blank=True, null=True, related_name='fuel_logs')
    fuel_date = models.DateField()
    liters = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_station = models.CharField(max_length=150)
    notes = models.TextField(blank=True)

    @property
    def fuel_consumption(self):
        # Liters consumed, can also compute consumption relative to distance
        return self.liters

    def __str__(self):
        return f"Fuel for {self.vehicle.registration_number} on {self.fuel_date}"
