from django.db import models
from vehicles.models import Vehicle

class Maintenance(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ('Routine Service', 'Routine Service'),
        ('Repair', 'Repair'),
        ('Inspection', 'Inspection'),
        ('Tire Change', 'Tire Change'),
        ('Engine Tuneup', 'Engine Tuneup'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenances')
    maintenance_type = models.CharField(max_length=50, choices=MAINTENANCE_TYPE_CHOICES)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')

    def __str__(self):
        return f"{self.maintenance_type} for {self.vehicle.registration_number}"
