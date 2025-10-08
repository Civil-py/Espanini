# listen_events.py
import json
import time
import requests
import threading
from requests.auth import HTTPDigestAuth
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand
from timesheets.models import Timesheets, Employees
from control_panel.models import Devices, Tenant
from timesheets.views import (
    get_hours_worked, get_overtime_one_device, get_overtime_two, get_normal_hours
)
from control_panel.db_manager import register_tenant_db
from p.p.routers import set_current_tenant, clear_current_tenant
from datetime import datetime


def process_event(event):
    """Process a single Hikvision event into the Timesheets table."""
    try:
        emp_no = event["employee_no"]
        status = event["attendance_status"]
        date_time_str = event["datetime"]
        device_name = event["device_name"]
        company = event["company"]

        if not emp_no or not status or not date_time_str:
            return

        dt = parse_datetime(date_time_str)
        if not dt:
            return

        date = dt.date()
        time_ = dt.time()

        # Find employee in this company
        employee = Employees.objects.filter(
            employee_id=emp_no,
            company=company
        ).first()

        if not employee:
            print(f"[{device_name}] No matching employee for ID {emp_no}")
            return

        # Handle checkIn
        if status.lower() == "checkin":
            Timesheets.objects.create(
                company=company,
                employee_id=emp_no,
                site=employee.site,
                date=date,
                clock_in=time_,
            )

            if not employee.connected or employee.connected.lower() != "yes":
                employee.connected = "yes"
                employee.save(update_fields=["connected"])
                print(f"[{device_name}] Employee {emp_no} marked as connected.")

            print(f"[{device_name}] CheckIn recorded for {emp_no} at {time_}")

        # Handle checkOut
        elif status.lower() == "checkout":
            ts = Timesheets.objects.filter(
                employee_id=emp_no,
                company=company,
                clock_out=None,
            ).first()

            if not ts or not ts.clock_in:
                print(f"[{device_name}] No matching checkIn found for {emp_no} on {date}")
                return

            hours_worked = get_hours_worked(ts.clock_in, time_)
            ts.clock_out = time_
            ts.hours_worked = hours_worked
            ts.normal_hours = get_normal_hours(hours_worked, date)
            ts.overtime_normal_saturdays = get_overtime_one_device(company,ts.clock_in, time_, ts.date)
            ts.overtime_holiday_sundays = get_overtime_two(hours_worked, ts.date)
            ts.save()

            print(f"[{device_name}] CheckOut recorded for {emp_no} at {time_}, hours={hours_worked}")

    except Exception as e:
        print(f"[{device_name}] Event processing error: {e}")


def listen_to_device(device, stdout, style):
    ip = device.ip_address
    username = device.username
    password = device.password

    # 🔑 Get tenant
    tenant = getattr(device, "tenant", None)

    url = f"http://{ip}/ISAPI/Event/notification/alertStream"
    auth = HTTPDigestAuth(username, password)

    stdout.write(style.SUCCESS(f"[{device.name}] Starting event listener on {ip}..."))

    while True:
        try:
            with requests.get(url, auth=auth, stream=True, timeout=60) as r:
                if r.status_code != 200:
                    stdout.write(style.WARNING(
                        f"[{device.name}] Stream error: {r.status_code}"
                    ))
                    time.sleep(5)
                    continue

                buffer = b""
                for raw in r.iter_content(chunk_size=1024):
                    buffer += raw
                    parts = buffer.split(b'--MIME_boundary')
                    buffer = parts.pop()

                    for part in parts:
                        try:
                            start = part.find(b'{')
                            end = part.rfind(b'}') + 1
                            if start == -1 or end == -1:
                                continue

                            json_bytes = part[start:end]
                            event_json = json.loads(json_bytes.decode('utf-8'))

                            evt = event_json.get("AccessControllerEvent") or event_json
                            name = evt.get("name")
                            emp_no = evt.get("employeeNoString")
                            attendance_status = evt.get("attendanceStatus")
                            date_time = event_json.get("dateTime") or evt.get("dateTime")

                            if emp_no is None:
                                continue

                            event = {
                                "device_name": device.name,
                                "employee_no": emp_no,
                                "datetime": date_time,
                                "attendance_status": attendance_status,
                                "company": device.company,
                            }

                            # 🔑 Activate tenant DB for ORM operations
                            if tenant:
                                try:
                                    register_tenant_db(tenant)
                                    set_current_tenant(tenant)
                                    process_event(event)
                                finally:
                                    clear_current_tenant()
                            else:
                                process_event(event)

                            stdout.write(
                                f"[{device.name}] name: {name}, "
                                f"Employee No: {emp_no}, "
                                f"dateTime: {date_time}, "
                                f"Attendance Status: {attendance_status}"
                            )

                        except Exception as inner_e:
                            stdout.write(style.WARNING(
                                f"[{device.name}] JSON decode/processing error: {inner_e}"
                            ))
                            continue

        except Exception as e:
            stdout.write(style.ERROR(f"[{device.name}] Stream exception: {e}"))
            time.sleep(5)


class Command(BaseCommand):
    help = "Listen to Hikvision Access Control events from all devices (threaded, tenant-aware)"

    def handle(self, *args, **kwargs):
        devices = Devices.objects.select_related("tenant").all()
        if not devices.exists():
            self.stdout.write(self.style.ERROR("No devices found in database."))
            return

        for device in devices:
            t = threading.Thread(
                target=listen_to_device,
                args=(device, self.stdout, self.style),
                daemon=True,
            )
            t.start()

        while True:
            time.sleep(1)
