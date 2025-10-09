# forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Tenant, PublicHolidays, Devices, Company

User = get_user_model()

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'db_alias', 'db_host', 'db_name', 'db_user', 'db_password', 'db_port', 'db_options', 'open', 'close']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_alias': forms.TextInput(attrs={'class': 'form-control'}),
            'db_host': forms.TextInput(attrs={'class': 'form-control'}),
            'db_name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_user': forms.TextInput(attrs={'class': 'form-control'}),
            'db_port': forms.TextInput(attrs={'class': 'form-control'}),
            'db_options': forms.TextInput(attrs={'class': 'form-control'}),
            'db_password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'company_rep', 'email', 'tier','open', 'close']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_rep': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'open': forms.TextInput(attrs={'class': 'form-control'}),
            'close': forms.TextInput(attrs={'class': 'form-control'}),
            'tier': forms.Select(attrs={'class': 'form-control'}),

        }

class PlatformUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username','company', 'email', 'tenant', 'role', 'password', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tenant': forms.Select(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])  # hash password
        if commit:
            user.save()
        return user

class PublicHolidaysForm(forms.ModelForm):
    class Meta:
        model = PublicHolidays
        fields = ['date']
        widgets = {
            'date': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Devices
        fields = [
            "name",
            "username",
            "password",
            "mac_address",
            "serial_number",
            "tenant",
            "company",
            "ip_address",
            "employees",
            "status",
            "firmware_version",
            "last_seen",
            "last_sync",
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.TextInput(attrs={'class': 'form-control'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'tenant': forms.Select(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'employees': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'firmware_version': forms.TextInput(attrs={'class': 'form-control'}),
            'last_seen': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'last_sync': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }