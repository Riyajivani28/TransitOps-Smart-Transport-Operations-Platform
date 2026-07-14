import os
import django
from datetime import date, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TransitOps.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from vehicles.models import Vehicle
from drivers.models import Driver
from trips.models import Trip
from maintenance.models import Maintenance
from fuel.models import FuelLog
from expenses.models import Expense

def seed():
    print("Flushing old data and seeding database with Indian Fleet records...")
    
    # Clear tables to prevent foreign key duplicate collisions
    Trip.objects.all().delete()
    FuelLog.objects.all().delete()
    Maintenance.objects.all().delete()
    Expense.objects.all().delete()
    Vehicle.objects.all().delete()
    Driver.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.all().delete()

    # 1. Create Users
    users_data = [
        ('admin', 'Admin', 'admin@transitops.com'),
        ('manager', 'Fleet Manager', 'manager@transitops.com'),
        ('dispatcher', 'Dispatcher', 'dispatcher@transitops.com'),
        ('safety', 'Safety Officer', 'safety@transitops.com'),
        ('finance', 'Financial Analyst', 'finance@transitops.com'),
    ]
    
    for username, role, email in users_data:
        user = User.objects.create_user(username=username, email=email, password='password123')
        user.is_staff = True
        if username in ['admin', 'manager']:
            user.is_superuser = True
        user.save()
        Profile.objects.create(user=user, role=role, phone='9876543210', raw_password='password123')
        print(f"Created user: {username} with role: {role}")

    # 2. Create Indian Vehicles
    vehicles_data = [
        ('MH-12-PQ-9876', 'Tata Intra V30', '2022', 'Light Truck', 1500, 45000, 320000.00, '2022-03-15', 'Available'),
        ('GJ-01-AB-1234', 'Mahindra Bolero Maxx', '2021', 'Light Truck', 3500, 78000, 450000.00, '2021-06-20', 'On Trip'),
        ('DL-03-XY-5678', 'BharatBenz 2823R', '2020', 'Heavy Truck', 18000, 120000, 950000.00, '2020-01-10', 'In Shop'),
        ('KA-04-LM-9012', 'Ashok Leyland Dost', '2023', 'Light Truck', 24000, 35000, 1400000.00, '2023-08-01', 'Available'),
        ('HR-26-CD-3456', 'Tata Ace Gold', '2019', 'Cargo Van', 1800, 150000, 280000.00, '2019-11-05', 'Retired'),
    ]

    vehicles = []
    for reg, name, model, v_type, capacity, odo, cost, p_date, status in vehicles_data:
        vehicle = Vehicle.objects.create(
            registration_number=reg,
            name=name,
            model=model,
            vehicle_type=v_type,
            max_load_capacity=capacity,
            current_odometer=odo,
            acquisition_cost=cost,
            purchase_date=p_date,
            status=status
        )
        vehicles.append(vehicle)
        print(f"Created vehicle: {reg}")

    # 3. Create Drivers with Indian Names
    drivers_data = [
        ('Rajesh Kumar', 'DL-12345678901', 'Heavy Vehicle', '2027-12-31', '9810012345', 'rajesh@transitops.com', 95, 'Sector 15, Dwarka, New Delhi', 'Sunita Kumar 9810012346', 'Available'),
        ('Amit Patel', 'GJ-98765432102', 'Heavy Vehicle', '2026-05-15', '9825098765', 'amit@transitops.com', 98, 'Satellite, Ahmedabad, Gujarat', 'Dinesh Patel 9825098766', 'On Trip'),
        ('Rohan Sharma', 'MH-45612345678', 'Light Vehicle', '2028-09-20', '9892011223', 'rohan@transitops.com', 85, 'Kothrud, Pune, Maharashtra', 'Anil Sharma 9892011224', 'Available'),
        ('Priya Mehta', 'KA-78945612300', 'Light Vehicle', '2025-11-10', '9740055667', 'priya@transitops.com', 90, 'Indiranagar, Bangalore, Karnataka', 'Sanjay Mehta 9740055668', 'Available'),
        ('Sanjay Gupta', 'UP-00001234567', 'Heavy Vehicle', '2024-01-01', '9935044332', 'sanjay@transitops.com', 60, 'Gomti Nagar, Lucknow, Uttar Pradesh', 'Mary Gupta 9935044333', 'Suspended'),
    ]

    drivers = []
    for name, lic_num, lic_cat, lic_exp, phone, email, safety, addr, emg, status in drivers_data:
        driver = Driver.objects.create(
            name=name,
            license_number=lic_num,
            license_category=lic_cat,
            license_expiry_date=lic_exp,
            phone=phone,
            email=email,
            safety_score=safety,
            address=addr,
            emergency_contact=emg,
            status=status
        )
        drivers.append(driver)
        print(f"Created driver: {name}")

    # 4. Create Trips (Indian Cities)
    v_bolero = Vehicle.objects.get(registration_number='GJ-01-AB-1234')
    v_ashok = Vehicle.objects.get(registration_number='KA-04-LM-9012')
    d_amit = Driver.objects.get(name='Amit Patel')
    d_rajesh = Driver.objects.get(name='Rajesh Kumar')

    trips_data = [
        ('TRIP-1001', 'Mumbai Warehouse', 'Pune Distribution Center', v_bolero, d_amit, 1200, 150, timezone.now() - timedelta(days=2), None, 'Dispatched', 'Urgent medical supplies dispatch'),
        ('TRIP-1002', 'JNPT Port Terminal', 'Mumbai Warehouse', v_ashok, d_rajesh, 22000, 450, timezone.now() - timedelta(days=5), timezone.now() - timedelta(days=4), 'Completed', 'Imported steel coil transport'),
        ('TRIP-1003', 'Ahmedabad Hub', 'Vadodara Outlet', v_ashok, d_rajesh, 5000, 80, timezone.now() + timedelta(days=1), None, 'Draft', 'Standard retail delivery schedule'),
    ]

    for trip_num, src, dest, veh, drv, weight, dist, start, end, status, notes in trips_data:
        Trip.objects.create(
            trip_number=trip_num,
            source=src,
            destination=dest,
            vehicle=veh,
            driver=drv,
            cargo_weight=weight,
            expected_distance=dist,
            start_date=start,
            end_date=end,
            status=status,
            notes=notes
        )
        print(f"Created trip: {trip_num}")

    # 5. Create Maintenance Logs
    v_benz = Vehicle.objects.get(registration_number='DL-03-XY-5678')
    m_data = [
        (v_benz, 'Routine Service', 'Engine Oil, Coolant & Air Filter Replacement', date.today() - timedelta(days=3), None, 3500.00, 'Open'),
        (v_bolero, 'Tire Change', 'Replaced all rear MRF tires', date.today() - timedelta(days=15), date.today() - timedelta(days=14), 12000.00, 'Closed'),
    ]

    for veh, m_type, desc, start, end, cost, status in m_data:
        Maintenance.objects.create(
            vehicle=veh,
            start_date=start,
            maintenance_type=m_type,
            description=desc,
            end_date=end,
            cost=cost,
            status=status
        )
        print(f"Created maintenance log for {veh.registration_number}")

    # 6. Create Fuel Logs
    t1002 = Trip.objects.filter(trip_number='TRIP-1002').first()
    f_logs = [
        (v_bolero, None, date.today() - timedelta(days=1), 80, 7200.00, 'IndianOil Pump, Pune', 'Routine refill'),
        (v_ashok, t1002, date.today() - timedelta(days=4), 150, 13500.00, 'Bharat Petroleum JNPT', 'Refuel during TRIP-1002 run'),
    ]

    for veh, trip, f_date, liters, cost, station, notes in f_logs:
        FuelLog.objects.create(
            vehicle=veh,
            fuel_date=f_date,
            liters=liters,
            cost=cost,
            trip=trip,
            fuel_station=station,
            notes=notes
        )
        print(f"Created fuel log for {veh.registration_number}")

    # 7. Create Expenses
    expenses_data = [
        (v_bolero, 'Fuel', 7200.00, date.today() - timedelta(days=1), 'Routine refill'),
        (v_ashok, 'Fuel', 13500.00, date.today() - timedelta(days=4), 'Refuel during TRIP-1002 run'),
        (v_bolero, 'Maintenance', 12000.00, date.today() - timedelta(days=14), 'Replaced all rear MRF tires'),
        (None, 'Insurance', 35000.00, date.today() - timedelta(days=30), 'Annual company fleet insurance premium'),
        (v_ashok, 'Toll', 450.00, date.today() - timedelta(days=4), 'Mumbai-Pune Expressway toll charges'),
    ]

    for veh, exp_type, amount, exp_date, remarks in expenses_data:
        Expense.objects.create(
            vehicle=veh,
            expense_type=exp_type,
            amount=amount,
            expense_date=exp_date,
            remarks=remarks
        )
        print(f"Created expense: {exp_type} - {amount}")

    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed()
