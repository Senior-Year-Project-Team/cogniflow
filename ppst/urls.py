from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("clinician/register/", views.clinician_register, name="clinician_register"),
    path("patient-entry/", views.patient_link_entry, name="patient_link_entry"),
    path("patient-access/", views.patient_access, name="patient_access"),
    path("test/instructions/", views.test_instructions, name="test_instructions"),
    path("test/actual/", views.test_actual, name="test_actual"),
    path("clinician/dashboard/", views.clinician_dashboard, name="clinician_dashboard"),
    path("clinician/export/example/", views.export_test_example, name="export_test_example"),
]
