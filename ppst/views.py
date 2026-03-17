import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg
from django.views.decorators.http import require_POST
from .models import TestSession, TrialResponse, Clinician


# ---------------------------------------------------------------------------
# Public / landing
# ---------------------------------------------------------------------------

def index(request):
    """Main landing page for CogniFlow platform."""
    return render(request, "ppst/index.html")


def patient_link_entry(request):
    """Page where a patient pastes the link provided by their clinician."""
    return render(request, "ppst/patient_link_entry.html")


# ---------------------------------------------------------------------------
# Clinician auth
# ---------------------------------------------------------------------------

def login(request):
    """Login page for clinicians."""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # Remember Me — extend session to 2 weeks if checkbox ticked
            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # expires on browser close
            return redirect("clinician_dashboard")
            # Invalid credentials — re-render with error
        return render(request, "ppst/login.html", {"error": "Invalid username or password."})

    return render(request, "ppst/login.html")

def logout_view(request):
    """Log out the current clinician and redirect to login."""
    
    logout(request)
    return redirect("login")

def clinician_register(request):
    """Registration page for new clinicians."""
    
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email     = request.POST.get("email", "").strip()
        password  = request.POST.get("password", "")
        confirm   = request.POST.get("password_confirm", "")

        # basic validation
        if not email:
            return render(request, "ppst/clinician_register.html", {"error": "Email is required."})
        if password != confirm:
            return render(request, "ppst/clinician_register.html", {"error": "Passwords do not match."})

        # Use email as username (simple and common)
        username = email.lower()

        if User.objects.filter(username=username).exists():
            return render(request, "ppst/clinician_register.html", {"error": "Account already exists."})

        # Split full name into first/last
        parts = full_name.split()
        first_name = parts[0] if parts else ""
        last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # institution not collected in your HTML, so leave blank
        Clinician.objects.create(user=user, institution="")

        return redirect("login")

    return render(request, "ppst/clinician_register.html")


# ---------------------------------------------------------------------------
# Patient flow
# ---------------------------------------------------------------------------

def _dob_to_age_bracket(dob_str):
    """
    Convert MM/DD/YYYY to the nearest age bracket string.
    Returns '' if the DOB is invalid or the patient is under 18.
    """
    from datetime import date
    try:
        # Handle both MM/DD/YYYY and YYYY-MM-DD formats
        if '-' in dob_str:
            year, month, day = dob_str.split("-")
        else:
            month, day, year = dob_str.split("/")
        dob = date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        return ""
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:   return ""
    elif age <= 24: return "18-24"
    elif age <= 34: return "25-34"
    elif age <= 44: return "35-44"
    elif age <= 54: return "45-54"
    elif age <= 64: return "55-64"
    elif age <= 74: return "65-74"
    elif age <= 84: return "75-84"
    else:           return "85+"


@require_POST
def generate_session(request):
    """
    Clinician submits language, voice, and the patient's DOB.
    DOB is converted to an age bracket server-side and then discarded —
    only the bracket is stored, preserving patient privacy.
    Returns the unique patient URL as JSON.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    language = request.POST.get("language", "en")
    voice    = request.POST.get("voice", "male")
    dob_str  = request.POST.get("dob", "")

    age_bracket = _dob_to_age_bracket(dob_str)
    if not age_bracket:
        return JsonResponse({"error": "Invalid or underage date of birth."}, status=400)

    clinician = getattr(request.user, "clinician", None)

    session = TestSession.objects.create(
        clinician=clinician,
        language=language,
        voice=voice,
        age_bracket=age_bracket,  # DOB converted and immediately discarded
    )

    patient_url = request.build_absolute_uri(
        reverse("patient_access", args=[session.access_token])
    )
    return JsonResponse({"url": patient_url, "token": str(session.access_token)})


def patient_access(request, access_token):
    """
    GET  — Patient opens the UUID link. Session already has all data the
           clinician entered (language, voice, age bracket). Just show a
           confirmation page and let them begin.
    POST — Patient clicks Begin. Store session info and redirect to instructions.
    """
    expiry_time = timezone.now() - timedelta(hours=48)
    session = get_object_or_404(
    TestSession,
    access_token=access_token,
    is_completed=False,
    created_at__gte=expiry_time)

    if request.method == "POST":
        request.session["test_session_id"] = session.pk
        request.session["language"]        = session.language
        request.session["voice"]           = session.voice
        return redirect("test_instructions")

    return render(request, "ppst/patient_access.html", {
        "language": session.language,
        "voice":    session.voice,
        "token":    str(session.access_token),
    })


def test_instructions(request):
    """Instructions page shown before the assessment begins."""
    return render(request, "ppst/instructions.html", {
        "language": request.session.get("language", "en"),
        "voice":    request.session.get("voice", "male"),
    })


def test_actual(request):
    """The live PPST assessment page."""
    context = {
        "language": request.session.get("language", "en"),
        "voice":    request.session.get("voice", "male"),
    }
    return render(request, "ppst/actual_test.html", context)


# ---------------------------------------------------------------------------
# PPST scoring helper
# ---------------------------------------------------------------------------

def _compute_correct_response(stimulus: list, trial_type: str) -> list:
    """
    Returns the expected PPST correct response for a given stimulus.

    Digit trials:  sort all symbols numerically ascending.
        e.g. ['9', '2', '5']  ->  ['2', '5', '9']

    Mixed trials:  digits ascending first, then letters alphabetically.
        e.g. ['T', '7', 'D', '4', 'N']  ->  ['4', '7', 'D', 'N', 'T']
    """
    if trial_type == "digit":
        return sorted(stimulus, key=lambda s: int(s))
    digits  = sorted([s for s in stimulus if s.isdigit()], key=lambda s: int(s))
    letters = sorted([s for s in stimulus if s.isalpha()])
    return digits + letters


# ---------------------------------------------------------------------------
# Result submission (called by JS fetch when the patient finishes)
# ---------------------------------------------------------------------------

@require_POST
def submit_results(request):
    """
    Receives the 12 trial results as JSON from actual_test.html and persists
    them to the database.

    Expected JSON body:
    {
        "results": [
            {
                "trialNumber":  1,
                "type":         "digit",
                "stimulus":     ["2", "9", "5"],
                "response":     ["2", "9", "5"],
                "correct":      true,
                "responseTime": 3241
            },
            ...  (12 total)
        ]
    }
    """
    # Retrieve the TestSession created in patient_access
    test_session_pk = request.session.get("test_session_id")
    if not test_session_pk:
        return JsonResponse({"error": "No active test session found."}, status=400)

    test_session = get_object_or_404(TestSession, pk=test_session_pk)

    # Prevent duplicate submissions
    if test_session.is_completed:
        return JsonResponse({"error": "Session already submitted."}, status=400)

    # Parse the JSON body sent by the browser
    try:
        payload = json.loads(request.body)
        results = payload.get("results", [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    if len(results) != 12:
        return JsonResponse(
            {"error": f"Expected 12 trial results, got {len(results)}."},
            status=400,
        )

    # Persist each trial response — score server-side using PPST rules
    for item in results:
        stimulus   = item["stimulus"]
        response   = item["response"]
        trial_type = item["type"]

        # Server-side PPST scoring (overrides any client-supplied 'correct' flag)
        correct_answer = _compute_correct_response(stimulus, trial_type)
        is_correct     = (response == correct_answer)

        TrialResponse.objects.create(
            session           = test_session,
            trial_number      = item["trialNumber"],
            trial_type        = trial_type,
            stimulus_sequence = ",".join(stimulus),
            patient_response  = ",".join(response),
            latency_ms        = item["responseTime"],
            is_correct        = is_correct,
        )

    # Mark the session as complete
    test_session.is_completed = True
    test_session.completed_at = timezone.now()
    test_session.save()

    # Clear the session key so it can't be reused
    del request.session["test_session_id"]

    return JsonResponse({"success": True})


# ---------------------------------------------------------------------------
# Clinician dashboard
# ---------------------------------------------------------------------------

@login_required(login_url="/login/")
def clinician_dashboard(request):
    """Dashboard for clinicians to view results and administer new tests."""

    clinician = getattr(request.user, "clinician", None)

    # Sessions belonging to this clinician
    all_sessions       = TestSession.objects.filter(clinician=clinician)
    completed_sessions = all_sessions.filter(is_completed=True)
    
    expiry_time = timezone.now() - timedelta(hours=48)
    pending_sessions = all_sessions.filter(
    is_completed=False,
    created_at__gte=expiry_time).order_by("-created_at")[:10]

    # Aggregate summary stats
    stats = TrialResponse.objects.filter(
        session__in=completed_sessions
    ).aggregate(mean_latency=Avg("latency_ms"))

    # Build per-session result rows
    recent_results = []
    for s in completed_sessions.order_by("-completed_at")[:20]:
        responses   = s.trial_responses.all()
        correct     = responses.filter(is_correct=True).count()
        avg_latency = responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0
        export_url  = request.build_absolute_uri(
            reverse("export_session", args=[s.access_token])
        )
        recent_results.append({
            "patient_id":      f"P-{s.pk:04d}",
            "age_bracket":     s.age_bracket,
            "avg_latency_ms":  round(avg_latency),
            "correct_percent": round(correct / 12 * 100),
            "export_url":      export_url,
        })

    total = completed_sessions.count()
    mean_correct = 0
    if total:
        all_responses = TrialResponse.objects.filter(session__in=completed_sessions)
        correct_total = all_responses.filter(is_correct=True).count()
        mean_correct  = round(correct_total / all_responses.count() * 100) if all_responses.count() else 0

    # Build pending session rows so the clinician can copy links they already generated
    pending_rows = []
    for s in pending_sessions:
        pending_rows.append({
            "token":      str(s.access_token),
            "language":   s.get_language_display(),
            "voice":      s.get_voice_display(),
            "created_at": s.created_at,
            "patient_url": request.build_absolute_uri(
                reverse("patient_access", args=[s.access_token])
            ),
        })

    # Age bracket stats — all completed tests in the system (population norms)
    all_completed = TestSession.objects.filter(is_completed=True)
    bracket_stats = []
    for bracket, label in TestSession.AGE_BRACKET_CHOICES:
        bracket_sessions = all_completed.filter(age_bracket=bracket)
        bracket_responses = TrialResponse.objects.filter(session__in=bracket_sessions)
        count = bracket_sessions.count()
        if count > 0:
            correct = bracket_responses.filter(is_correct=True).count()
            total_responses = bracket_responses.count()
            avg_lat = bracket_responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0
            correct_pct = round(correct / total_responses * 100) if total_responses else 0
            bracket_stats.append({
                "bracket":      label,
                "count":        count,
                "correct_pct":  correct_pct,
                "avg_latency":  round(avg_lat),
            })

    context = {
        "total_tests":          total,
        "mean_correct_percent": mean_correct,
        "mean_latency_ms":      round(stats["mean_latency"] or 0),
        "age_bracket_count":    completed_sessions.values("age_bracket").distinct().count(),
        "recent_results":       recent_results,
        "pending_rows":         pending_rows,
        "bracket_stats":        bracket_stats,
        "generate_url":         request.build_absolute_uri(reverse("generate_session")),
    }
    return render(request, "ppst/clinician_dashboard.html", context)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

@login_required(login_url="/login/")
def export_session(request, access_token):
    clinician = getattr(request.user, "clinician", None)
    session   = get_object_or_404(TestSession, access_token=access_token, clinician=clinician)
    responses = session.trial_responses.all()

    # ── Session info header ───────────────────────────────────────────
    lines = [
        f"# CogniFlow PPST — Session Report",
        f"# Patient ID:,P-{session.pk:04d}",
        f"# Age Bracket:,{session.age_bracket}",
        f"# Language:,{session.get_language_display()}",
        f"# Test Date:,{session.completed_at.strftime('%Y-%m-%d %H:%M') if session.completed_at else 'N/A'}",
        f"#",
    ]

    # ── Raw trial data ────────────────────────────────────────────────
    lines.append("trial_number,trial_type,stimulus,response,correct,latency_ms")
    for r in responses:
        lines.append(
            f"{r.trial_number},{r.trial_type},"
            f"\"{r.stimulus_sequence}\","
            f"\"{r.patient_response}\","
            f"{r.is_correct},{r.latency_ms}"
        )

    # ── Derived outcome measures ──────────────────────────────────────
    total_trials    = responses.count()
    correct_trials  = responses.filter(is_correct=True).count()
    digit_responses = responses.filter(trial_type="digit")
    mixed_responses = responses.filter(trial_type="mixed")

    correct_pct     = round(correct_trials / total_trials * 100) if total_trials else 0
    avg_latency     = round(responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0)
    digit_correct   = digit_responses.filter(is_correct=True).count()
    mixed_correct   = mixed_responses.filter(is_correct=True).count()
    digit_pct       = round(digit_correct / digit_responses.count() * 100) if digit_responses.count() else 0
    mixed_pct       = round(mixed_correct / mixed_responses.count() * 100) if mixed_responses.count() else 0
    avg_digit_lat   = round(digit_responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0)
    avg_mixed_lat   = round(mixed_responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0)

    # Age bracket population comparison
    bracket_sessions   = TestSession.objects.filter(is_completed=True, age_bracket=session.age_bracket)
    bracket_responses  = TrialResponse.objects.filter(session__in=bracket_sessions)
    bracket_correct    = bracket_responses.filter(is_correct=True).count()
    bracket_total      = bracket_responses.count()
    bracket_avg_pct    = round(bracket_correct / bracket_total * 100) if bracket_total else 0
    bracket_avg_lat    = round(bracket_responses.aggregate(avg=Avg("latency_ms"))["avg"] or 0)

    lines += [
        f"#",
        f"# ── Derived Outcome Measures ──────────────────",
        f"# Overall correct %:,{correct_pct}%",
        f"# Overall avg latency:,{avg_latency} ms",
        f"# Digit trials correct %:,{digit_pct}%",
        f"# Mixed trials correct %:,{mixed_pct}%",
        f"# Digit avg latency:,{avg_digit_lat} ms",
        f"# Mixed avg latency:,{avg_mixed_lat} ms",
        f"#",
        f"# ── Age Bracket Comparison ({session.age_bracket}) ──────────",
        f"# Bracket avg correct %:,{bracket_avg_pct}%",
        f"# Bracket avg latency:,{bracket_avg_lat} ms",
        f"# Bracket sample size:,{bracket_sessions.count()} tests",
    ]

    content  = "\n".join(lines) + "\n"
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="ppst_session_{session.pk}.csv"'
    )
    return response


def export_test_example(request):
    """Return a small hardcoded CSV as a demo export."""
    content = (
        "trial_number,trial_type,stimulus,response,correct,latency_ms\n"
        '1,digit,"2,9,5","2,9,5",True,2134\n'
        '2,digit,"7,3,1,8","7,3,8,1",False,3891\n'
    )
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ppst_example_result.csv"'
    return response
