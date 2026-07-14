from django.db import models

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('On Trip', 'On Trip'),
        ('In Shop', 'In Shop'),
        ('Retired', 'Retired'),
    ]

    VEHICLE_TYPE_CHOICES = [
        ('Cargo Van', 'Cargo Van'),
        ('Light Truck', 'Light Truck'),
        ('Heavy Truck', 'Heavy Truck'),
        ('Semi-Trailer', 'Semi-Trailer'),
    ]

    registration_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPE_CHOICES)
    max_load_capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum Load Capacity (kg)")
    current_odometer = models.PositiveIntegerField(help_text="Current Odometer (km)")
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.registration_number})"
