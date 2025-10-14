from django import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from control_panel.models import PlatformUser
from .models import Sites, Employees, SiteManagers, Timesheets
from p.p.routers import get_current_tenant

User = get_user_model()


# --------------------------
# TimeSheets Form
# --------------------------
class TimeSheetsForm(ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super(TimeSheetsForm, self).__init__(*args, **kwargs)
        self.user = user  # ✅ store logged in user

    class Meta:
        model = Timesheets
        exclude = ['company']  # ✅ hide company from form
        widgets = {
            'employee_id': forms.HiddenInput(),
            'site': forms.HiddenInput(),
            'hours_worked': forms.HiddenInput(),
            'normal_hours': forms.HiddenInput(),
            'overtime_normal_saturdays': forms.HiddenInput(),
            'overtime_holiday_sundays': forms.HiddenInput(),
            'signed_off': forms.HiddenInput(),
            'signed_off_by': forms.HiddenInput(),
            'date': forms.TextInput(attrs={'class': 'form-control'}),
            'clock_in': forms.TextInput(attrs={'class': 'form-control'}),
            'clock_out': forms.TextInput(attrs={'class': 'form-control'}),

        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and hasattr(self.user, "company"):
            instance.company = self.user.company  # ✅ assign company
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# --------------------------
# Employees Form
# --------------------------
class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['created_date'].widget.attrs['readonly'] = True
        self.fields['last_updated'].widget.attrs['readonly'] = True

        # Determine the DB to query
        if self.user and self.user.company_id:
            if hasattr(self.user, "tenant") and self.user.tenant:
                db_alias = self.user.tenant.db_alias
            else:
                db_alias = "default"

            # Build the queryset
            queryset = Sites.objects.using(db_alias).filter(company_id=self.user.company_id)

            # DEBUG
            print("EmployeeForm __init__ debug:")
            print("DB alias:", db_alias)
            print("Sites queryset SQL:", queryset.query)

            # Replace the site field
            self.fields['site'] = forms.ModelChoiceField(
                queryset=queryset,
                widget=forms.Select(attrs={'class': 'form-control'}),
                required=False
            )


    class Meta:
        model = Employees
        exclude = ['company']
        widgets = {
            'created_date': forms.HiddenInput(),
            'last_updated': forms.HiddenInput(),
            'connected': forms.HiddenInput(),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'wage': forms.TextInput(attrs={'class': 'form-control'}),
            'site': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and hasattr(self.user, "company"):
            instance.company = self.user.company


        if commit:
            # Save to tenant DB if user has tenant, else default
            if hasattr(self.user, 'tenant') and self.user.tenant:
                instance.save(using=self.user.tenant.db_alias)
            else:
                instance.save()
            self.save_m2m()
        return instance

# --------------------------
# Sites Form
# --------------------------
class SiteForm(ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.user = user
        self.fields['site_id'].widget.attrs['readonly'] = True
        self.fields['created_date'].widget.attrs['readonly'] = True
        self.fields['last_updated'].widget.attrs['readonly'] = True

    class Meta:
        model = Sites
        exclude = ['company']  # ✅ hide company
        widgets = {
            'software_id': forms.TextInput(attrs={'class': 'form-control'}),
            'created_date': forms.HiddenInput(),
            'last_updated': forms.HiddenInput(),
            'site_id': forms.HiddenInput(),
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and hasattr(self.user, "company"):
            instance.company = self.user.company
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# --------------------------
# Site Managers Form
# --------------------------
class SiteManagersForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SiteManagers
        exclude = ['company']
        fields = ['site', 'employee', 'assigned', 'username']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-control'}),
            'assigned': forms.HiddenInput(),
            'employee': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user and getattr(self.user, "company_id", None):
            # ✅ Determine correct DB alias
            db_alias = (
                self.user.tenant.db_alias
                if hasattr(self.user, "tenant") and self.user.tenant
                else "default"
            )

            # ✅ Filter Sites by company
            site_queryset = Sites.objects.using(db_alias).filter(company_id=self.user.company_id)
            self.fields["site"] = forms.ModelChoiceField(
                queryset=site_queryset,
                widget=forms.Select(attrs={"class": "form-control"}),
                required=False,
                label="Site",
            )

            # ✅ Filter Employees by company
            employee_queryset = Employees.objects.using(db_alias).filter(company_id=self.user.company_id)
            self.fields["employee"] = forms.ModelChoiceField(
                queryset=employee_queryset,
                widget=forms.Select(attrs={"class": "form-control"}),
                required=False,
                label="Employee",
            )

            # Optional: Debugging info
            print("SiteManagersForm __init__ debug:")
            print("DB alias:", db_alias)
            print("Sites queryset SQL:", site_queryset.query)
            print("Employees queryset SQL:", employee_queryset.query)

    def save(self, commit=True):
        tenant = get_current_tenant()

        # ✅ Create Django User in default DB
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            email=self.cleaned_data["email"],
        )
        user.role = "site_manager"
        user.company = self.user.company if self.user and hasattr(self.user, "company") else None
        if tenant:
            user.tenant = tenant
        user.save(using="default")

        # ✅ Create SiteManager in tenant DB
        site_manager = super().save(commit=False)
        site_manager.user_id = user.id
        site_manager.username = user.username
        if self.user and hasattr(self.user, "company"):
            site_manager.company = self.user.company

        if commit:
            if tenant:
                site_manager.save(using=tenant.db_alias)
            else:
                site_manager.save()
            self.save_m2m()

        return site_manager


class UploadFileForm(forms.Form):
    file = forms.FileField()