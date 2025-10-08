from django.contrib import admin
from .models import Employees, Timesheets, Sites, SiteManagers

# Register your models here.
admin.site.register(Employees)
admin.site.register(Sites)
admin.site.register(SiteManagers)
admin.site.register(Timesheets)
