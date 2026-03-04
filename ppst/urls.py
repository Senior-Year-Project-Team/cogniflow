from django.urls import path
from . import views

urlpatterns = [
    # Landing
    path("",                              views.index,               name="index"),

    # Clinician auth
    path("login/",                        views.login,               name="login"),
    path("clinician/register/",           views.clinician_register,  name="clinician_register"),

    # Clinician dashboard, session generation & exports
    path("clinician/dashboard/",          views.clinician_dashboard, name="clinician_dashboard"),
    path("clinician/generate-session/",   views.generate_session,    name="generate_session"),
    path("clinician/export/example/",     views.export_test_example, name="export_test_example"),
    path("clinician/export/<uuid:access_token>/",
                                          views.export_session,      name="export_session"),

    # Patient flow — UUID in URL ties the patient to the pre-created session
    path("patient-entry/",                views.patient_link_entry,  name="patient_link_entry"),
    path("patient/<uuid:access_token>/",  views.patient_access,      name="patient_access"),
    path("test/instructions/",            views.test_instructions,   name="test_instructions"),
    path("test/actual/",                  views.test_actual,         name="test_actual"),

    # Result submission (called by JS fetch at end of test)
    path("test/submit/",                  views.submit_results,      name="submit_results"),
]
