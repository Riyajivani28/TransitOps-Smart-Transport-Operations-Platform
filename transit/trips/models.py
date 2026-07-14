from django.db import models
from vehicles.models import Vehicle
from drivers.models import Driver

class Trip(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Dispatched', 'Dispatched'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    trip_number = models.CharField(max_length=50, unique=True)
    source = models.CharField(max_length=150)
    destination = models.CharField(max_length=150)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trips')
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cargo Weight (kg)")
    expected_distance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Expected Distance (km)")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Trip {self.trip_number}: {self.source} -> {self.destination}"
