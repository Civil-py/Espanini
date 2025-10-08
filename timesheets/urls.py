from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path('timesheets/media/<path:path>', views.media_files, name='media_files'),
    path('timesheets/user-profile/<str:user>', views.profile, name='profile'),

    path("pay-roll-data", views.payroll_data, name="payroll_data"),
    path('payroll-data-pdf/<str:start_date>/<str:end_date>/', views.payroll_data_pdf, name='payroll_data_pdf'),
    path('payroll-data-excel/<str:start_date>/<str:end_date>/', views.payroll_data_excel, name='payroll_data_excel'),


    path('logout/', views.logout_view, name='logout'),

    path("employees", views.employees, name="employees"),
    path('add-employee/', views.add_employee, name="add_employee"),
    path('view-employee/<int:id>', views.view_employee, name="view_employee"),
    path('edit-employee/<int:id>', views.edit_employee, name="edit_employee"),
    path('delete-employee/<int:id>/<str:employee_id>', views.delete_employee, name="delete_employee"),


    path("sites", views.sites, name="sites"),
    path('add-site/', views.add_site, name="add_site"),
    path('view-site/<str:site_id>', views.view_site, name="view_site"),
    path('edit-site/<str:site_id>', views.edit_site, name="edit_site"),
    path('delete-site/<str:site_id>', views.delete_site, name="delete_site"),


    path('add-site-managers/<str:site_id>', views.add_site_managers, name="add_site_managers"),
    path('view-site-managers/<str:site_id>', views.view_site_managers, name="view_site_managers"),
    path('view-site-manager/<str:site_id>/<int:id>', views.view_site_manager, name="view_site_manager"),
    path('delete-site/<str:site_id>/<int:id>', views.delete_site_manager, name="delete_site_manager"),


    path("timesheets", views.timesheets, name="timesheets"),
    path('add-timesheet/', views.add_timesheet, name="add_timesheet"),
    path('timesheet-upload/', views.timesheet_upload, name="timesheet-upload"),
    path('employees-upload/', views.employees_upload, name="employees-upload"),
    path('upload', views.upload, name="upload"),

    path('view_site_employees/<str:site_id>', views.view_site_employees, name="view_site_employees"),
    path('view_site_employees', views.view_unknown_site_employees, name="view_unknown_site_employees"),
    path('view_employee_timesheets/<int:id>/<str:site_id>', views.view_employee_timesheets, name="view_employee_timesheets"),
    path('add_employee_timesheet/<int:id>', views.add_employee_timesheet, name="add_employee_timesheet"),
    path('edit_employee_timesheet/<int:id>', views.edit_employee_timesheet, name="edit_employee_timesheet"),
    path('view_employee_unknown_site_timesheets/<int:id>/<str:employee_id>', views.view_employee_unknown_timesheets, name="view_employee_unknown_timesheets"),

    path('all_employee_timesheets/<int:id>/<str:employee_id>', views.all_employee_timesheets, name="all_employee_timesheets"),


    path('view-timesheet/<int:id>', views.view_timesheet, name="view_timesheet"),
    path('delete-timesheet/<int:id>', views.delete_timesheet, name="delete_timesheet"),
    path('sign-timesheet/<int:id>', views.sign_off_timesheet, name="sign_off_timesheet"),
    path('timesheets/bulk-sign-off/<str:employee_id>/<str:site_id>', views.bulk_sign_off_timesheets, name='bulk_sign_off_timesheets'),
    path('timesheets/bulk-sign-off-unknown/<str:employee_id>/', views.bulk_sign_off_unknown_timesheets, name='bulk_sign_off_unknown_timesheets'),
    path('download-template/', views.download_template, name='download_template'),

    path('download-employees-template/', views.download_employees_template, name='download_employees_template'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)