from django.contrib import admin
from .models import Clinician, TestSession, TrialResponse


@admin.register(Clinician)
class ClinicianAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "created_at")


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("access_token", "clinician", "age_bracket", "language", "voice", "is_completed", "created_at")
    list_filter  = ("is_completed", "language", "age_bracket")


@admin.register(TrialResponse)
class TrialResponseAdmin(admin.ModelAdmin):
    list_display = ("session", "trial_number", "trial_type", "is_correct", "latency_ms")
    list_filter  = ("is_correct", "trial_type")
