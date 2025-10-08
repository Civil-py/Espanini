from django.urls import path
from . import views, views_admin


urlpatterns = [

    path('login-view/', views.tenant_login, name='login-view'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),

    path('api/webhook/attendance/', views.attendance_webhook, name='attendance_webhook'),

    path("companies/", views_admin.company_list, name="company_list"),
    path("company/add/", views_admin.company_create, name="company_create"),
    path("company/edit/<int:id>", views_admin.edit_company, name="edit_company"),

    path("tenants/", views_admin.tenant_list, name="tenant_list"),
    path("tenants/add/", views_admin.tenant_create, name="tenant_create"),
    path("tenants/edit/<int:id>", views_admin.edit_tenant, name="edit_tenant"),

    path("users/", views_admin.user_list, name="user_list"),
    path("users/add/", views_admin.user_create, name="user_create"),
    path("users/edit/<int:id>", views_admin.edit_user, name="edit_user"),

    path("public-holidays/", views_admin.public_holidays, name="public-holidays"),
    path("add-public-holiday/", views_admin.add_public_holiday, name="add-public-holiday"),
    path("delete-public-holiday/<int:id>", views_admin.delete_public_holiday, name="delete-public-holiday"),


    path("devices/", views_admin.device_list, name="device_list"),
    path("devices/add/", views_admin.device_create, name="device_create"),
    path("device/edit/<int:id>", views_admin.device_edit, name="edit_device"),
    path("device/delete/<int:id>", views_admin.device_delete, name="delete_device"),

    path("my-devices/", views_admin.tenant_device_list, name="tenant_device_list"),
    path("test-devices/", views_admin.test_device, name="test_device"),
    path("test-event-stream/", views_admin.test_event_stream, name="test_device"),

    ]