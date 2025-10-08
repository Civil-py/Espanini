from django.contrib import admin
from .models import Tenant, PlatformUser

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'db_alias', 'db_host',)

@admin.register(PlatformUser)
class PlatformUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'tenant')

