# views_admin.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import TenantForm, PlatformUserForm, PublicHolidaysForm, DeviceForm, CompanyForm
from .models import Tenant, PlatformUser, PublicHolidays, Devices, Company
from django.contrib.auth import get_user_model
from django.contrib import messages
from p.p.routers import get_current_tenant
from .db_manager import register_tenant_db
from django.core.management import call_command
from django.http import  HttpResponse
import json

import requests
from requests.auth import HTTPDigestAuth

from .utils import tenant_admin_required

User = get_user_model()


# Restrict to platform admins
def platform_admin_required(user):
    return user.is_authenticated and user.role == 'platform_admin'


@login_required
@user_passes_test(platform_admin_required)
def company_list(request):
    companies = Company.objects.all()
    return render(request, "control_panel/company_list.html", {"companies": companies})

@login_required
@user_passes_test(platform_admin_required)
def company_create(request):
    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("company_list")
    else:
        form = CompanyForm()
    return render(request, "control_panel/company_form.html", {"form": form})


@login_required
@user_passes_test(platform_admin_required)
def edit_company(request, id):
    company = get_object_or_404(Company, id=id)

    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {company.name} updated successfully.")
            return redirect("company_list")  # adjust to your user list route
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CompanyForm(instance=company)

    return render(request, "control_panel/edit_company.html", {"form": form, "company": company})



@login_required
@user_passes_test(platform_admin_required)
def tenant_list(request):
    tenants = Tenant.objects.all()
    return render(request, "control_panel/tenant_list.html", {"tenants": tenants})

@login_required
@user_passes_test(platform_admin_required)
def tenant_create(request):
    if request.method == "POST":
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant_instance = form.save(commit=False)

            # Assign DB fields
            tenant_instance.db_alias = form.cleaned_data['db_alias'].strip()
            tenant_instance.db_host = form.cleaned_data['db_host']
            tenant_instance.db_name = form.cleaned_data['db_name']
            tenant_instance.db_user = form.cleaned_data['db_user']
            tenant_instance.db_password = form.cleaned_data['db_password']

            # 1️⃣ Save tenant first
            tenant_instance.save()

            # 2️⃣ Register tenant DB and run migrations
            register_tenant_db(tenant_instance, migrate=True)

            return redirect("tenant_list")
    else:
        form = TenantForm()

    return render(request, "control_panel/tenant_form.html", {"form": form})

@login_required
@user_passes_test(platform_admin_required)
def user_list(request):
    users = PlatformUser.objects.all()
    return render(request, "control_panel/user_list.html", {"users": users})


@login_required
@user_passes_test(platform_admin_required)
def user_create(request):
    if request.method == "POST":
        form = PlatformUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("user_list")
    else:
        form = PlatformUserForm()
    return render(request, "control_panel/user_form.html", {"form": form})


@login_required
@user_passes_test(platform_admin_required)
def edit_user(request, id):
    user = get_object_or_404(User, pk=id)

    if request.method == "POST":
        form = PlatformUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully.")
            return redirect("user_list")  # adjust to your user list route
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PlatformUserForm(instance=user)

    return render(request, "control_panel/edit_user.html", {"form": form, "user": user})

@login_required
@user_passes_test(platform_admin_required)
def edit_tenant(request, id):
    tenant = get_object_or_404(Tenant, pk=id)

    if request.method == "POST":
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Tenant {tenant.name} updated successfully.")
            return redirect("tenant_list")  # adjust this to your tenants list view
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TenantForm(instance=tenant)

    return render(request, "control_panel/edit_tenant.html", {"form": form, "tenant": tenant})

@login_required
@user_passes_test(platform_admin_required)
def public_holidays(request):
    public_holidays = PublicHolidays.objects.all()
    return render(request, "control_panel/public_holidays.html", {"public_holidays": public_holidays})

@login_required
@user_passes_test(platform_admin_required)
def add_public_holiday(request):
    if request.method == "POST":
        form = PublicHolidaysForm(request.POST, )
        if form.is_valid():
            form.save()
            messages.success(request, 'New public holiday added')
            return redirect("public-holidays")
    else:
        form = PublicHolidaysForm()  # Correctly instantiate the form when GET request

    return render(request, "control_panel/add_public_holidays.html", {
        'form': form
    })

@login_required
@user_passes_test(platform_admin_required)
def delete_public_holiday(request, id):
    public_holiday = PublicHolidays.objects.get(id=id)
    public_holiday.delete()
    return redirect("public-holidays")


@login_required
@user_passes_test(platform_admin_required)
def device_list(request):
    devices = Devices.objects.all()
    return render(request, "control_panel/device_list.html", {"devices": devices})

@login_required
@user_passes_test(platform_admin_required)
def device_create(request):
    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Device added successfully.")
            return redirect("device_list")
    else:
        form = DeviceForm()
    return render(request, "control_panel/device_form.html", {"form": form})

@login_required
@user_passes_test(platform_admin_required)
def device_edit(request, id):
    device = get_object_or_404(Devices, pk=id)
    if request.method == "POST":
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, f"Device {device.name} updated successfully.")
            return redirect("device_list")
    else:
        form = DeviceForm(instance=device)
    return render(request, "control_panel/device_form.html", {"form": form, "device": device})

@login_required
@user_passes_test(platform_admin_required)
def device_delete(request, id):
    device = get_object_or_404(Devices, pk=id)
    device.delete()
    messages.success(request, "Device deleted successfully.")
    return redirect("device_list")


@login_required
@user_passes_test(tenant_admin_required)
def tenant_device_list(request):
    devices = Devices.objects.filter(tenant=get_current_tenant(), company=request.user.company)

    return render(request, "timesheets/devices.html", {"devices": devices})




def test_device(request):
    url = "http://192.168.0.206/ISAPI/System/deviceInfo"
    auth = HTTPDigestAuth("admin", "sammotha64")
    r = requests.get(url, auth=auth, timeout=5)
    return HttpResponse(f"Status: {r.status_code}, Body: {r.text}")




import xml.etree.ElementTree as ET
import time

def test_event_stream(request):
    listen_to_device("192.168.0.206", "admin", "sammotha64")
    return HttpResponse("Listening... check your server logs")


def listen_to_device(ip, username, password):
    url = f'http://{ip}/ISAPI/Event/notification/alertStream'  # common path; confirm in docs
    auth = HTTPDigestAuth(username, password)

    try:
        with requests.get(url, auth=auth, stream=True, timeout=60) as r:
            r.raise_for_status()
            # r.iter_lines() yields byte lines; ISAPI may send chunks of xml
            for raw in r.iter_lines(decode_unicode=False):
                if not raw:
                    continue
                chunk = raw.decode(errors='ignore').strip()
                # Some devices send fragments; try to build complete XML or find <Event>...</Event>
                if '<Event' in chunk or '<Notification' in chunk:
                    try:
                        # try parse chunk directly
                        root = ET.fromstring(chunk)
                    except ET.ParseError:
                        # If chunk is incomplete, you could buffer until complete XML is received.
                        continue

                    # Example: find common fields (adjust based on actual payload)
                    device_serial = root.findtext('.//deviceSerialNumber') or root.findtext('.//deviceID')
                    event_type = root.findtext('.//eventType') or root.findtext('.//EventType')
                    event_time = root.findtext('.//dateTime') or root.findtext('.//EventTime')
                    print("evt:", device_serial, event_type, event_time)
                    # then call your handler to save to DB
    except Exception as e:
        print("stream error:", e)
        time.sleep(5)
        # reopen loop or exit




