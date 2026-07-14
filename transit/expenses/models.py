from django.db import models
from vehicles.models import Vehicle

class Expense(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('Fuel', 'Fuel'),
        ('Maintenance', 'Maintenance'),
        ('Toll', 'Toll'),
        ('Parking', 'Parking'),
        ('Insurance', 'Insurance'),
        ('Other', 'Other'),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, related_name='expenses')
    expense_type = models.CharField(max_length=50, choices=EXPENSE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    remarks = models.TextField(blank=True)

    def __str__(self):
        v_reg = self.vehicle.registration_number if self.vehicle else "General"
        return f"{self.expense_type} - {self.amount} ({v_reg})"
