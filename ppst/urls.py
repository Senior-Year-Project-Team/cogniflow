from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    # Landing
    path("",                              views.index,               name="index"),

    # Clinician auth
    path("login/",                        views.login,               name="login"),
    path("logout/",                       views.logout_view,         name="logout"),
    path("clinician/register/",           views.clinician_register,  name="clinician_register"),

    # Password reset (Django built-in flow, customized for CogniFlow)
    path("password-reset/",
         auth_views.PasswordResetView.as_view(
             template_name="ppst/password_reset.html",
             email_template_name="ppst/password_reset_email.html",
             html_email_template_name="ppst/password_reset_email.html",
             subject_template_name="ppst/password_reset_subject.txt",
             extra_email_context={"site_name": "CogniFlow"},
         ),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="ppst/password_reset_done.html"),
         name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="ppst/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("password-reset-complete/",
         auth_views.PasswordResetCompleteView.as_view(template_name="ppst/password_reset_complete.html"),
         name="password_reset_complete"),

    # Clinician dashboard, session generation & exports
    path("clinician/dashboard/",          views.clinician_dashboard, name="clinician_dashboard"),
    path("clinician/generate-session/",   views.generate_session,    name="generate_session"),
    path("clinician/export/example/",     views.export_test_example, name="export_test_example"),
    path("clinician/report/<uuid:access_token>/preview/",
         views.preview_session_report, name="preview_session_report"),
    path("clinician/export/<uuid:access_token>/",
         views.export_session,      name="export_session"),

    # Patient flow — UUID in URL ties the patient to the pre-created session
    path("patient/<uuid:access_token>/",  views.patient_access,      name="patient_access"),
    path("test/instructions/",            views.test_instructions,   name="test_instructions"),
    path("test/actual/",                  views.test_actual,         name="test_actual"),

    # Result submission (called by JS fetch at end of test)
    path("test/submit/",    views.submit_results,      name="submit_results"),
]