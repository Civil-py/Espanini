import json
from datetime import datetime, timedelta
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
        print("🔍 Top-level keys in incoming JSON:", list(raw_event.keys()))

        # ✅ Try to locate AccessControllerEvent even if nested
        event_data = None
        if "AccessControllerEvent" in raw_event:
            event_data = raw_event
        elif "event_log" in raw_event and "AccessControllerEvent" in raw_event["event_log"]:
            event_data = raw_event["event_log"]
        else:
            # Try to search deeper if nested oddly
            for key, val in raw_event.items():
                if isinstance(val, dict) and "AccessControllerEvent" in val:
                    event_data = val
                    break

        if event_data:
            mac_address = event_data.get("macAddress")
            inner = event_data.get("AccessControllerEvent", {})
            date_time_str = event_data.get("dateTime")
            status = inner.get("attendanceStatus", "undefined")
            emp_no = (
                inner.get("employeeNoString")
                or inner.get("employeeNo")
                or inner.get("employeeID")
                or inner.get("verifyNo")
                or "unknown"
            )

            print(f"🧩 AccessControllerEvent keys: {list(inner.keys())}")
            print(f"➡️ Extracted employee_no: {emp_no}")

        else:
            print("⚠️ No AccessControllerEvent key found in JSON, falling back to manual payload")
            mac_address = raw_event.get("mac_address")
            date_time_str = raw_event.get("datetime")
            status = raw_event.get("attendance_status")
            emp_no = raw_event.get("employeeNoString") or "unknown"


        # 🧩 Validation
        if not (emp_no and status and date_time_str and mac_address):
            print(f"⚠️ Missing required fields -> emp_no={emp_no}, status={status}, datetime={date_time_str}, mac={mac_address}")
            return {"status": "error", "message": "Missing required fields"}

        dt = parse_datetime(date_time_str)
        if not dt:
            print(f"⚠️ Invalid datetime: {date_time_str}")
            return {"status": "error", "message": "Invalid datetime format"}

        date = dt.date()
        time_ = dt.time()

        # 🔗 Lookup device
        device = Devices.objects.filter(mac_address=mac_address).select_related("tenant").first()
        if not device:
            print(f"❌ No device found for MAC {mac_address}")
            return {"status": "error", "message": f"Device with MAC {mac_address} not found"}

        tenant = getattr(device, "tenant", None)
        print(f"🏢 Device: {device.name}, MAC: {device.mac_address}, Tenant: {tenant}, Company: {device.company}")

        # 🧠 If tenant is null, use default DB
        if tenant:
            try:
                print(f"🔄 Switching to tenant DB: {tenant}")
                register_tenant_db(tenant)
                set_current_tenant(tenant)
                result = _process_event_in_tenant(device, emp_no, status, date, time_, )
                print(f"✅ Tenant processing result: {result}")
                return result
            finally:
                clear_current_tenant()
        else:
            print("⚙️ No tenant set. Using default DB.")
            result = _process_event_in_tenant(device, emp_no, status, date, time_, )
            print(f"✅ Default DB processing result: {result}")
            return result

    except Exception as e:
        print(f"💥 process_event() exception: {e}")
        return {"status": "error", "message": str(e)}




def _process_event_in_tenant(device, emp_no, status, date, time_):
    """Logic that writes to Timesheets in the correct tenant DB."""
    company = device.company
    print(f"👷 Looking up employee: {emp_no} in company: {company} ")

    employee = Employees.objects.filter(employee_id=emp_no, company=company).first()

    if not employee:
        print(f"🚫 No employee found with ID={emp_no} for company={company}")
        return {"status": "error", "message": f"No matching employee {emp_no}"}

    # ✅ Always update last_seen on event
    device.last_seen = datetime.now()
    device.save(update_fields=["last_seen"])
    print(f"📡 Device '{device.name}' last_seen updated at {device.last_seen}")

    # ✅ Check-in
    if status.lower() == "checkin":
        duplicate = Timesheets.objects.filter(
            company=company,
            employee_id=emp_no,
            site=employee.site,
            date=date,
            clock_in__gte=(datetime.combine(date, time_) - timedelta(minutes=1)).time(),
            clock_in__lte=(datetime.combine(date, time_) + timedelta(minutes=1)).time(),
        ).exists()

        if duplicate:
            print(f"⚠️ Duplicate event ignored for employee {emp_no} at {time_}")
            return {"status": "ok", "message": "Duplicate event ignored"}

        Timesheets.objects.create(
            company=company,
            employee_id=emp_no,
            site=employee.site,
            date=date,
            clock_in=time_,
        )
        print(f"🕓 CheckIn recorded for {emp_no} at {time_}")

        current_connected = (employee.connected or "").lower().strip()
        if current_connected != "yes":
            employee.connected = "yes"
            employee.save(update_fields=["connected"])
            print(f"✅ Employee {employee.employee_id} marked as connected.")
        else:
            print(f"ℹ️ Employee {employee.employee_id} already marked as connected.")

        return {"status": "ok", "message": f"CheckIn for {emp_no} recorded"}

    # ✅ Check-out
    elif status.lower() == "checkout":
        ts = Timesheets.objects.filter(
            employee_id=emp_no, company=company, clock_out=None
        ).first()
        if not ts:
            print(f"⚠️ No open timesheet for employee {emp_no}")
            return {"status": "error", "message": f"No checkIn found for {emp_no}"}

        hours_worked = get_hours_worked(ts.clock_in, time_)
        ts.clock_out = time_
        ts.hours_worked = hours_worked
        ts.normal_hours = get_normal_hours(hours_worked, ts.date)
        ts.overtime_normal_saturdays = get_overtime_one_device(company, ts.clock_in, time_, ts.date)
        ts.overtime_holiday_sundays = get_overtime_two(hours_worked, ts.date)
        ts.save()

        print(f"🕔 CheckOut recorded for {emp_no} at {time_} | Hours worked: {hours_worked}")
        return {"status": "ok", "message": f"CheckOut for {emp_no} recorded"}

    else:
        print(f"⚠️ Unknown attendance status: '{status}'")
        return {"status": "error", "message": f"Unknown status '{status}'"}
