import uuid
from django.db import models
from django.contrib.auth.models import User


class Clinician(models.Model):
    """
    Extends Django's built-in User model with clinician-specific fields.
    Each clinician has a one-to-one relationship with a User account.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="clinician")
    institution = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Clinician: {self.user.get_full_name() or self.user.username}"


class TestSession(models.Model):
    """
    Represents one patient's test session.
    Created by a clinician; the access token is shared with the patient as a link.
    No personally identifiable information is stored — only an age bracket.
    """

    AGE_BRACKET_CHOICES = [
        ("18-24",  "18–24"),
        ("25-34",  "25–34"),
        ("35-44",  "35–44"),
        ("45-54",  "45–54"),
        ("55-64",  "55–64"),
        ("65-74",  "65–74"),
        ("75-84",  "75–84"),
        ("85+",    "85+"),
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Spanish"),
    ]

    VOICE_CHOICES = [
        ("male",   "Male"),
        ("female", "Female"),
        ("none",   "No Voice"),
    ]

    # Unique token used to generate the patient access link
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # The clinician who created this session (nullable so sessions survive clinician deletion)
    clinician = models.ForeignKey(
        Clinician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )

    age_bracket = models.CharField(max_length=10, choices=AGE_BRACKET_CHOICES)
    language    = models.CharField(max_length=5,  choices=LANGUAGE_CHOICES, default="en")
    voice       = models.CharField(max_length=10, choices=VOICE_CHOICES,    default="male")

    is_completed = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "completed" if self.is_completed else "pending"
        return f"Session {self.access_token} [{status}]"


class TrialResponse(models.Model):
    """
    Stores a patient's response for a single trial within a TestSession.
    One TestSession will have exactly 12 TrialResponse rows when complete.
    """

    TRIAL_TYPE_CHOICES = [
        ("digit", "Digit Only"),
        ("mixed", "Mixed Digit-Letter"),
    ]

    session      = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name="trial_responses")

    trial_number = models.PositiveSmallIntegerField()          # 1–12
    trial_type   = models.CharField(max_length=10, choices=TRIAL_TYPE_CHOICES)

    # Stored as comma-separated strings, e.g. "2,9,5"
    stimulus_sequence  = models.CharField(max_length=50)   # correct answer
    patient_response   = models.CharField(max_length=50)   # what the patient clicked

    latency_ms = models.PositiveIntegerField()             # milliseconds from grid display to submit
    latencies_ms = models.CharField(max_length=200, blank=True, default="")  # per-click latencies, comma-separated
    is_correct = models.BooleanField()

    class Meta:
        ordering = ["trial_number"]
        unique_together = [("session", "trial_number")]    # one response per trial per session

    def __str__(self):
        result = "✓" if self.is_correct else "✗"
        return f"Session {self.session.access_token} | Trial {self.trial_number} {result}"
