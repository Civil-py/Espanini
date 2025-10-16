from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.management import call_command


from .db_manager import register_tenant_db

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    company_rep = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True)
    open = models.TimeField(null=True, blank=True)
    close = models.TimeField(null=True, blank=True)
    sunday_is_normal_workday = models.BooleanField(default=False)

    tier = models.CharField(max_length=50, choices=[
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} "

class Tenant(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, )
    open = models.TimeField(null=True, blank=True)
    close = models.TimeField(null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    db_alias = models.CharField(max_length=100, unique=True)
    db_host = models.CharField(max_length=255)
    db_name = models.CharField(max_length=255)
    db_user = models.CharField(max_length=255)
    db_password = models.CharField(max_length=255)
    db_port = models.IntegerField(default=5432)  # Default Postgres port
    db_options = models.CharField(max_length=255, blank=True, null=True)  # Extra options like sslmode

    db_engine = models.CharField(
        max_length=100,
        default="django.db.backends.postgresql",
        help_text="Django DB engine path"
    )

    time_zone = models.CharField(
        max_length=50,
        default="Africa/Johannesburg",
        help_text="IANA timezone (e.g. 'UTC', 'Africa/Johannesburg')"
    )
    health_con = models.CharField(
        max_length=50,
        default="good",
        help_text="Health status of tenant DB connection"
    )

    def __str__(self):
        return self.name

class PlatformUser(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    role = models.CharField(max_length=50, choices=[
        ('platform_admin', 'Platform Admin'),
        ('tenant_admin', 'Tenant Admin'),
        ('site_manager', 'Site Manager'),
    ])

class PublicHolidays(models.Model):
    date = models.DateField(null=True, blank=True)

@receiver(post_save, sender=Tenant, dispatch_uid="tenant_post_save")
def create_tenant_db(sender, instance, created, **kwargs):
    if created:
        register_tenant_db(instance)


class Devices(models.Model):
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255,)
    mac_address = models.CharField(max_length=50, unique=True, null=True, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    employees = models.IntegerField(null=True, blank=True, default=None)
    last_seen = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, choices=[("active", "Active"), ("inactive", "Inactive"), ("offline", "Offline")], default="active")
    firmware_version = models.CharField(max_length=100, blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
