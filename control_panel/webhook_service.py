# control_panel/webhook_service.py
import json
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from timesheets.models import Timesheets, Employees
from control_panel.models import Devices, Tenant
from control_panel.db_manager import register_tenant_db
from p.p.routers import set_current_tenant, clear_current_tenant
from timesheets.views import (
    get_hours_worked, get_overtime_one_device, get_overtime_two, get_normal_hours
)

def process_event(event):
    """Process a single Hikvision event into Timesheets."""
    try:
        emp_no = event.get("employee_no")
        status = event.get("attendance_status")
        date_time_str = event.get("datetime")
        device_sn = event.get("device_sn")  # device serial or name

        if not (emp_no and status and date_time_str and device_sn):
            return {"status": "error", "message": "Missing required fields"}

        dt = parse_datetime(date_time_str)
        if not dt:
            return {"status": "error", "message": "Invalid datetime format"}

        date = dt.date()
        time_ = dt.time()

        # Lookup device and tenant
        device = Devices.objects.filter(serial_no=device_sn).select_related("tenant").first()
        if not device:
            return {"status": "error", "message": f"Device {device_sn} not found"}

        tenant = getattr(device, "tenant", None)

        # Activate tenant DB
        if tenant:
            try:
                register_tenant_db(tenant)
                set_current_tenant(tenant)
                return _process_event_in_tenant(device, emp_no, status, date, time_)
            finally:
                clear_current_tenant()
        else:
            return _process_event_in_tenant(device, emp_no, status, date, time_)

    except Exception as e:
        return {"status": "error", "message": str(e)}

def _process_event_in_tenant(device, emp_no, status, date, time_):
    """Logic that writes to Timesheets in the correct tenant DB."""
    company = device.company
    employee = Employees.objects.filter(employee_id=emp_no, company=company).first()
    if not employee:
        return {"status": "error", "message": f"No matching employee {emp_no}"}

    if status.lower() == "checkin":
        Timesheets.objects.create(
            company=company,
            employee_id=emp_no,
            site=employee.site,
            date=date,
            clock_in=time_,
        )
        if employee.connected.lower() != "yes":
            employee.connected = "yes"
            employee.save(update_fields=["connected"])
        return {"status": "ok", "message": f"CheckIn for {emp_no} recorded"}

    elif status.lower() == "checkout":
        ts = Timesheets.objects.filter(
            employee_id=emp_no, company=company, clock_out=None
        ).first()
        if not ts:
            return {"status": "error", "message": f"No checkIn found for {emp_no}"}

        hours_worked = get_hours_worked(ts.clock_in, time_)
        ts.clock_out = time_
        ts.hours_worked = hours_worked
        ts.normal_hours = get_normal_hours(hours_worked, date)
        ts.overtime_normal_saturdays = get_overtime_one_device(company, ts.clock_in, time_, date)
        ts.overtime_holiday_sundays = get_overtime_two(hours_worked, date)
        ts.save()
        return {"status": "ok", "message": f"CheckOut for {emp_no} recorded"}

    else:
        return {"status": "error", "message": f"Unknown status '{status}'"}
