# p/p/middleware.py
from django.db import connections
from .routers import set_current_tenant, get_current_tenant, clear_current_tenant
from control_panel.models import PlatformUser, Tenant
from control_panel.db_manager import  register_tenant_db


class TenantMiddleware:
    """
    Ensures the current tenant is set for each request and its DB connection is alive.
    Falls back to default DB only for platform admins or if tenant DB fails.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        session_alias = request.session.get("tenant_alias", "default")

        # 1️⃣ Prioritize logged-in user's assigned tenant
        if request.user.is_authenticated:
            user_tenant = getattr(request.user, "tenant", None)
            if user_tenant:
                tenant = user_tenant
                session_alias = tenant.db_alias
                request.session["tenant_alias"] = session_alias
            else:
                session_alias = "default"
                request.session["tenant_alias"] = "default"

        # 2️⃣ Restore tenant from session if not already set
        if not tenant and session_alias != "default":
            try:
                tenant = Tenant.objects.get(db_alias=session_alias)
            except Tenant.DoesNotExist:
                tenant = None

        # 3️⃣ Set thread-local tenant (always string alias)
        active_alias = getattr(tenant, "db_alias", session_alias) if tenant else session_alias
        set_current_tenant(active_alias)

        # 4️⃣ Auto-register tenant DB if missing
        if active_alias != "default" and active_alias not in connections.databases:
            try:
                if not tenant:
                    tenant = Tenant.objects.get(db_alias=active_alias)
                register_tenant_db(tenant)
                print(f"🔄 Tenant DB '{active_alias}' auto-registered")
            except Exception as e:
                print(f"❌ Failed to auto-register tenant DB '{active_alias}': {e}")

        # 5️⃣ Ensure tenant DB connection is alive
        if active_alias != "default":
            try:
                conn = connections[active_alias]
                conn.ensure_connection()
                print(f"✅ Tenant DB '{active_alias}' connected: {conn.is_usable()}")
            except Exception as e:
                print(f"❌ Failed to connect tenant DB '{active_alias}': {e}")

        response = self.get_response(request)

        # 6️⃣ Clear thread-local tenant
        clear_current_tenant()
        return response


class DebugTenantMiddleware:
    """
    Debug middleware to show active tenant and DB connections.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_alias = request.session.get("tenant_alias")
        thread_alias = get_current_tenant()

        print("====== Tenant Debug ======")
        print(f"🟡 Session tenant_alias: {session_alias}")
        print(f"🟢 Thread-local tenant_alias: {thread_alias}")

        if thread_alias and thread_alias != "default":
            try:
                tenant = Tenant.objects.get(db_alias=thread_alias)
                print(f"✅ Active tenant object: {tenant} (tz={tenant.time_zone})")
            except Tenant.DoesNotExist:
                print("❌ No Tenant object found for thread-local alias")
        else:
            print("⚠️ Using default DB")

        for alias in connections:
            conn = connections[alias]
            print(f"  DB: {alias} -> Connected: {conn.is_usable()}")

        print("==========================")

        return self.get_response(request)
