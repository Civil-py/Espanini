# db_manager.py
from django.conf import settings
from django.core.management import call_command
import threading
import pytz
from django.utils import timezone
import logging
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations.executor import MigrationExecutor
from django.db import connections

logger = logging.getLogger(__name__)

# Thread-local storage for current tenant
THREAD_LOCAL = threading.local()



def migrate_app(app_label, alias):
    """
    Apply **all migrations** for a given app on a specific database alias.
    """
    connection = connections[alias]
    executor = MigrationExecutor(connection)
    # plan contains all migrations needed to bring app up-to-date
    targets = executor.loader.graph.leaf_nodes(app_label)
    plan = executor.migration_plan(targets)
    executor.migrate(plan)


def build_tenant_config(tenant):
    config = settings.DB_DEFAULTS.copy()

    tenant_config = {
        "ENGINE": getattr(tenant, "db_engine", "django.db.backends.postgresql"),
        "NAME": getattr(tenant, "db_name", settings.DATABASES["default"]["NAME"]),
        "USER": getattr(tenant, "db_user", settings.DATABASES["default"]["USER"]),
        "PASSWORD": getattr(tenant, "db_password", settings.DATABASES["default"]["PASSWORD"]),
        "HOST": getattr(tenant, "db_host", settings.DATABASES["default"]["HOST"]),
        "PORT": getattr(tenant, "db_port", settings.DATABASES["default"]["PORT"]),
        "ATOMIC_REQUESTS": True,
        "TIME_ZONE": getattr(tenant, "time_zone", settings.TIME_ZONE) or settings.TIME_ZONE,
    }

    db_options = getattr(tenant, "db_options", None)
    tenant_config["OPTIONS"] = db_options if isinstance(db_options, dict) else {"sslmode": "require"}

    config.update(tenant_config)

    return config


def register_tenant_db(tenant, migrate=False):
    alias = tenant.db_alias.strip()

    # Build DB config
    config = build_tenant_config(tenant)
    db_config = {k: v for k, v in config.items() if not k.startswith("_")}
    db_config.setdefault("TIME_ZONE", getattr(settings, "TIME_ZONE", "UTC"))

    # Delete old connection if exists
    if alias in connections:
        try:
            connections[alias].close()
        except Exception:
            pass
        del connections[alias]

    # Register new DB
    settings.DATABASES[alias] = db_config
    conn = connections[alias]
    conn.ensure_connection()

    # Activate tenant timezone
    tz = config.get("_TENANT_TIME_ZONE", settings.TIME_ZONE)
    timezone.activate(pytz.timezone(tz))

    if migrate:
        print(f"[DEBUG] Running migrations for tenant DB alias='{alias}'")


        # Run all migrations for this tenant DB
        call_command("migrate", database=alias, interactive=False, verbosity=1)
        print(f"[DEBUG] ✅ All migrations finished for tenant '{alias}'")




def activate_tenant_timezone(tenant):
    """
    Activate tenant-specific timezone.
    """
    tz = pytz.timezone(getattr(tenant, "time_zone", settings.TIME_ZONE))
    timezone.activate(tz)


def run_dynamic_migrations(db_config: dict):
    """
    Run migrations on a DB config without adding it to settings.DATABASES permanently.
    """
    alias = "dynamic_tenant"

    # Ensure TIME_ZONE is set
    if "TIME_ZONE" not in db_config or not db_config["TIME_ZONE"]:
        db_config["TIME_ZONE"] = getattr(settings, "TIME_ZONE", "UTC")
        print(f"[DEBUG] TIME_ZONE missing, defaulting to {db_config['TIME_ZONE']}")

    # Register temporary connection
    connections.databases[alias] = db_config
    print(f"[DEBUG] Registered temporary DB '{alias}' for migrations")

    try:
        conn = connections[alias]
        conn.ensure_connection()
        print(f"[DEBUG] Connection ensured for {alias} (Connected: {conn.is_usable()})")

        # Ensure migrations table exists
        recorder = MigrationRecorder(conn)
        recorder.ensure_schema()
        print("[DEBUG] MigrationRecorder schema ensured")

        # Load migrations
        executor = MigrationExecutor(conn)
        all_migrations = executor.loader.graph.leaf_nodes()
        print(f"[DEBUG] Migration targets (leaf nodes): {all_migrations}")

        # Apply migrations
        executor.migrate(all_migrations)
        print(f"[DEBUG] ✅ Migrations applied on DB {db_config['NAME']}")

        # Show applied migrations
        applied = recorder.applied_migrations()
        print(f"[DEBUG] Applied migrations ({len(applied)}): {applied}")

    finally:
        # Clean up
        del connections[alias]
        print(f"[DEBUG] Connection '{alias}' removed from connections")
