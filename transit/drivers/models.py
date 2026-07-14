from django.db import models
from django.utils import timezone

class Driver(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('On Trip', 'On Trip'),
        ('Off Duty', 'Off Duty'),
        ('Suspended', 'Suspended'),
    ]

    LICENSE_CATEGORY_CHOICES = [
        ('A', 'Class A CDL'),
        ('B', 'Class B CDL'),
        ('C', 'Class C CDL'),
        ('D', 'Class D Standard'),
    ]

    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='drivers/', blank=True, null=True)
    license_number = models.CharField(max_length=50, unique=True)
    license_category = models.CharField(max_length=20, choices=LICENSE_CATEGORY_CHOICES)
    license_expiry_date = models.DateField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    safety_score = models.PositiveIntegerField(default=100, help_text="Driver Safety Score (0-100)")
    address = models.TextField()
    emergency_contact = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')

    @property
    def is_license_expired(self):
        return self.license_expiry_date < timezone.now().date()

    def __str__(self):
        return self.name
