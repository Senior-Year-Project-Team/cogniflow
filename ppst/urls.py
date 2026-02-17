from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("patient-access/", views.patient_access, name="patient_access"),
    path("test/instructions/",views.test_instructions, name="test_instructions"),
    path("test/actual/", views.test_actual, name="test_actual"),
    path("clinician/dashboard/", views.clinician_dashboard, name="clinician_dashboard"),
    
]
