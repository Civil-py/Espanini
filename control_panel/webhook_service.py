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


def process_event(raw_event):
    """Process a single Hikvision event into Timesheets."""
    try:
        # 🔍 Detect if it's a Hikvision structured payload (nested under AccessControllerEvent)
        if "AccessControllerEvent" in raw_event:
            mac_address = raw_event.get("macAddress")
            inner = raw_event.get("AccessControllerEvent", {})
            date_time_str = raw_event.get("dateTime")
            status = inner.get("attendanceStatus", "undefined")
            emp_no = (
                    inner.get("employeeNoString")
                    or inner.get("employeeNo")
                    or inner.get("verifyNo")
            )

        else:
            # 🔹 Standard JSON payload (from manual curl test)
            mac_address = raw_event.get("mac_address")
            date_time_str = raw_event.get("datetime")
            status = raw_event.get("attendance_status")
            emp_no = raw_event.get("employee_no")

        # 🧩 Validate
        if not (emp_no and status and date_time_str and mac_address):
            return {"status": "error", "message": "Missing required fields"}

        dt = parse_datetime(date_time_str)
        if not dt:
            return {"status": "error", "message": "Invalid datetime format"}

        date = dt.date()
        time_ = dt.time()

        # 🔗 Lookup device by MAC first
        device = Devices.objects.filter(mac_address=mac_address).select_related("tenant").first()
        if not device:
            return {"status": "error", "message": f"Device with MAC {mac_address} not found"}

        tenant = getattr(device, "tenant", None)

        # 🧠 Handle tenant DB if needed
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

    # ✅ Check-in
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

    # ✅ Check-out
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

    # 🚫 Unknown status
    else:
        return {"status": "error", "message": f"Unknown status '{status}'"}
