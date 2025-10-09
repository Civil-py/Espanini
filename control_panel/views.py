from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from p.p.routers import set_current_tenant
from django.contrib import messages
from .db_manager import register_tenant_db, activate_tenant_timezone
from control_panel.models import PlatformUser, Tenant

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .webhook_service import process_event
import json

from django.utils import timezone



def index(request):
    return render(request, "control_panel/index.html")


def logout_view(request):
    logout(request)
    timezone.deactivate()  # reset back to default
    return redirect("index")


def tenant_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Step 1: Try to find the user in the default DB first
        try:
            user = PlatformUser.objects.using("default").get(username=username)
            tenant = user.tenant  # FK to Tenant (may be None)
        except PlatformUser.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return render(request, "control_panel/login.html")

        # Step 2: Authenticate *before* switching tenants
        user = authenticate(request, username=username, password=password)
        if not user:
            messages.error(request, "Invalid username or password.")
            return render(request, "control_panel/login.html")

        # Step 3: Login user
        login(request, user)

        # Step 4: Handle tenant setup *after* login
        if tenant:
            register_tenant_db(tenant, migrate=False)
            set_current_tenant(tenant.db_alias)
            request.session["tenant_alias"] = tenant.db_alias
            activate_tenant_timezone(tenant)
        else:
            set_current_tenant(None)
            request.session["tenant_alias"] = "default"
            timezone.deactivate()

        # Step 5: Redirect appropriately
        if user.role == "platform_admin":
            return redirect("user_list")
        return redirect("timesheets")

    return render(request, "control_panel/login.html")

# control_panel/views.py




@csrf_exempt
def attendance_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        # Handle multipart/form-data (used by Hikvision devices sometimes)
        if "event_log" in request.FILES or "event_log" in request.POST:
            raw_json = request.POST.get("event_log") or request.FILES["event_log"].read().decode("utf-8")
            print("🔍 Raw event_log JSON:", raw_json)
            data = json.loads(raw_json)
        else:
            # Fallback: raw JSON in body
            body = request.body.decode("utf-8")
            print("🔍 Raw body:", body)
            data = json.loads(body)

    except Exception as e:
        print("⚠️ Webhook parse error:", e)
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

    try:
        # Hikvision payload structure varies — adjust these as needed
        event = data.get("AccessControllerEvent", {})
        mac_address = (
            event.get("macAddress")
            or data.get("macAddress")
            or event.get("deviceMac")
            or "UnknownMAC"
        )

        result = process_event({
            "employee_no": event.get("serialNo", "unknown"),  # TODO: map this to your employee_id field if needed
            "attendance_status": event.get("attendanceStatus", "undefined"),
            "datetime": data.get("dateTime") or event.get("dateTime"),
            "mac_address": mac_address,
        })

        return JsonResponse(result)

    except Exception as e:
        print("⚠️ Webhook processing error:", e)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
