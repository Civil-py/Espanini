import threading
from django.conf import settings
from django.db import connections
from control_panel.models import Tenant, Company
from control_panel.db_manager import build_tenant_config, register_tenant_db  # reuse same builder

THREAD_LOCAL = threading.local()

def provision_tenant(tenant: Tenant):
    # Register DB if not connected
    register_tenant_db(tenant, migrate=True)

    # Copy company into tenant DB if missing
    if tenant.company:
        db_alias = tenant.db_alias
        company = tenant.company

        if not Company.objects.using(db_alias).filter(pk=company.pk).exists():
            Company.objects.using(db_alias).create(
                id=company.pk,  # keep same PK for consistency
                name=company.name,
                plan=company.plan,
                # ... any other fields
            )
            print(f"✅ Company {company} synced into tenant DB {db_alias}")

def set_current_tenant(value):
    """
    Accepts either a Tenant object or an alias (string).
    Stores both tenant and alias in thread-local storage.
    Ensures DB connection config is registered.
    """
    tenant = None
    alias = None

    if isinstance(value, Tenant):
        tenant = value
        alias = tenant.db_alias
    elif isinstance(value, str):
        alias = value
        if alias and alias != "default":
            try:
                tenant = Tenant.objects.get(db_alias=alias)
            except Tenant.DoesNotExist:
                tenant = None

    THREAD_LOCAL.tenant = tenant
    THREAD_LOCAL.tenant_alias = alias

    # Auto-register DB if needed
    if alias and alias != "default" and alias not in connections.databases:
        try:
            tenant_for_db = tenant or Tenant.objects.get(db_alias=alias)
            config = build_tenant_config(tenant_for_db)
            connections.databases[alias] = config
        except Tenant.DoesNotExist:
            pass


def get_current_tenant(request=None, return_alias=False, allow_default=True):
    """
    Returns the current tenant object (default).
    If return_alias=True, returns the alias string instead.
    """
    tenant = getattr(THREAD_LOCAL, "tenant", None)
    alias = getattr(THREAD_LOCAL, "tenant_alias", None)

    # Try fallback to session if nothing in thread-local
    if not tenant and request:
        alias = request.session.get("tenant_alias")
        if alias and alias != "default":
            try:
                tenant = Tenant.objects.get(db_alias=alias)
            except Tenant.DoesNotExist:
                tenant = None

    if return_alias:
        return alias or ("default" if allow_default else None)

    if tenant:
        return tenant
    if allow_default:
        return None  # explicitly None means "use default DB"
    raise RuntimeError("No tenant set for this request.")

def clear_current_tenant():
    """
    Clears tenant info (best practice at end of each request).
    """
    if hasattr(THREAD_LOCAL, "tenant"):
        del THREAD_LOCAL.tenant
    if hasattr(THREAD_LOCAL, "tenant_alias"):
        del THREAD_LOCAL.tenant_alias




class TenantRouter:
    core_apps = ["auth", "admin", "sessions", "contenttypes", "control_panel"]
    tenant_apps = ["timesheets"]

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.core_apps:
            return "default"
        return get_current_tenant(return_alias=True) or "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.core_apps:
            return "default"
        return get_current_tenant(return_alias=True) or "default"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Always migrate core apps to default
        if db == "default":
            return app_label in self.core_apps + self.tenant_apps  # ✅ allow timesheets too

        # Tenant DB gets core + tenant apps
        elif db and db.startswith("tenant_"):
            return app_label in self.core_apps + self.tenant_apps

        return False

