# control_panel/roles.py
from django.contrib.auth.decorators import user_passes_test


def is_platform_admin(user):
    return user.is_superuser or user.role == "platform_admin"

def is_tenant_admin(user):
    return user.role == "tenant_admin"

def is_site_manager(user):
    return user.role == "site_manager"

def role_required(*roles):
    def check(user):
        return user.is_authenticated and (
            user.is_superuser or user.role in roles
        )
    return user_passes_test(check)

# Predefined decorators
platform_admin_required = role_required("platform_admin")
tenant_admin_required = role_required("tenant_admin")
site_manager_required = role_required("site_manager")
