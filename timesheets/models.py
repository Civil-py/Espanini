from django.db import models
from django.conf import settings
from control_panel.models import Company

from django.template.defaultfilters import slugify
from django.utils import timezone
from uuid import uuid4


import datetime
from datetime import timezone

LICENSE_TYPES = [
    ('L', 'Lease'),
    ('W', 'Warranty'),
('M', 'Maintenance')
]

SOFTWARE_TYPES = [
    ('OP', 'On-platform'),
    ('C', 'Cloud')
]

RENEWAL_TYPES = [
    ('RE', 'Renewed'),
    ('NO', 'Not Renewed')
]

DEPARTMENT_TYPES = [
    ('JUR', 'Junior'),
    ('Mid', 'Middle Management'),
    ('SEN', 'Senior Management')
]

CATEGORY_TYPES = [
    ('SS', 'System'),
    ('APP', 'Application'),
('MID', 'Middleware'),
('OF', 'Office')
]

SIGNEDOFF = [
    ('Yes', 'Yes'),
    ('No', 'No'),

]

GENDER = [
    ('Male', 'Male'),
    ('Female', 'Female'),

]


# Create your models here.



class Sites(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    site_id = models.CharField(  max_length=64, primary_key=True)
    site_name = models.CharField(max_length=64)
    site_address = models.CharField(null=True,  max_length=64)


    #utility Fields
    created_date = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.site_name}"

        if self.created_date is None:
            self.created_date = datetime.datetime.today().now()
        self.last_updated = datetime.datetime.today().now()

        super(Sites, self).save(*args, **kwargs)

class Employees(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=64, null=True)
    first_name = models.CharField(max_length=64, null=True)
    last_name = models.CharField(max_length=64,null=True)
    id_number = models.CharField(max_length=64,null=True)
    gender = models.CharField(max_length=64, null=True, choices=GENDER)
    email = models.EmailField(null=True)
    department = models.CharField(max_length=64, null=True, choices=DEPARTMENT_TYPES)
    position = models.CharField(max_length=64, null=True)
    wage = models.FloatField(null=True, blank=True)
    site = models.ForeignKey(Sites, models.CASCADE, blank=True, null=True)
    connected = models.CharField(max_length=64, null=True, blank=True)
    # utility Fields
    created_date = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.created_date is None:
            self.created_date = datetime.datetime.today().now()
        self.last_updated = datetime.datetime.today().now()

        super(Employees, self).save(*args, **kwargs)



class SiteManagers(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)

    user_id = models.IntegerField(null=True, blank=True)  # ID of the user in default DB
    username = models.CharField(max_length=150, null=True, blank=True)  # Optional convenience field


    assigned = models.DateTimeField(null=True, blank=True)
    employee = models.ForeignKey(Employees, models.CASCADE, )
    site = models.ForeignKey(Sites, models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.employee} - {self.username or 'No User'}"


class Timesheets(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=64, null=True)
    site = models.ForeignKey(Sites, models.CASCADE, blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    hours_worked = models.FloatField(null=True, blank=True, default=None)
    normal_hours = models.FloatField(null=True, blank=True, default=None)
    overtime_normal_saturdays = models.FloatField(null=True, blank=True, default=None)
    overtime_holiday_sundays = models.FloatField(null=True, blank=True, default=None)
    signed_off  = models.CharField(max_length=64, null=True, blank=True)
    signed_off_by = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"{self.employee_id} @ {self.site} on {self.date}"

    @property
    def formatted_date(self):
        return self.date.strftime('%d-%m-%Y') if self.date else ''


class UserDatabase(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    db_alias = models.CharField(max_length=100)  # e.g., 'tenant_user1'

    # Optional, for later dynamic config
    db_host = models.CharField(max_length=255, blank=True, null=True)
    db_name = models.CharField(max_length=255, blank=True, null=True)
    db_user = models.CharField(max_length=255, blank=True, null=True)
    db_password = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} → {self.db_alias}"






