from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse

def index(request):
    """Main landing page for CogniFlow platform"""
    return render(request, "ppst/index.html")

def patient_link_entry(request):
    """Page where patient pastes or enters the link provided by their clinician"""
    return render(request, "ppst/patient_link_entry.html")

def login(request):
    """Login page for clinicians and administrators"""
    if request.method == "POST":
        # Demo: accept any credentials and redirect to dashboard
        return redirect("clinician_dashboard")
    return render(request, "ppst/login.html")


def clinician_register(request):
    """Registration page for clinicians (demo – does not persist users)"""
    if request.method == "POST":
        # In a real app, you would create the user account here.
        # For this demo, redirect to the login page after "creating" the account.
        return redirect("login")
    return render(request, "ppst/clinician_register.html")

def patient_access(request):
    """Patient access page — collects language, DOB, and voice preference"""
    return render(request, "ppst/patient_access.html")

def test_instructions(request):
    """Instructions page; receives language/dob/voice from patient_access form"""
    if request.method == "POST":
        request.session["language"] = request.POST.get("language", "en")
        request.session["dob"]      = request.POST.get("dob", "")
        request.session["voice"]    = request.POST.get("voice", "male")
    return render(request, "ppst/instructions.html")

def test_actual(request):
    """Actual PPST assessment page"""
    context = {
        "language": request.session.get("language", "en"),
        "voice":    request.session.get("voice", "male"),
    }
    return render(request, "ppst/actual_test.html", context)

def clinician_dashboard(request):
    """Dashboard for clinicians to view results and manage tests"""
    example_export_url = request.build_absolute_uri(reverse("export_test_example"))
    recent_results = [
        {
            "patient_id": "P-0001",
            "age_bracket": "65–74",
            "avg_latency_ms": 1234,
            "correct_percent": 92,
            "export_url": example_export_url,
        }
    ]
    context = {
        "total_tests":          1,
        "mean_correct_percent": 92,
        "mean_latency_ms":      1234,
        "age_bracket_count":    1,
        "recent_results":       recent_results,
        "is_test_giver":        True,
        "patient_access_link":  request.build_absolute_uri("/patient-access/"),
    }
    return render(request, "ppst/clinician_dashboard.html", context)


def export_test_example(request):
    """Return a small CSV file as an example per-patient export."""
    content = (
        "patient_id,age_bracket,avg_latency_ms,correct_percent\n"
        "P-0001,65-74,1234,92\n"
    )
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ppst_example_result.csv"'
    return response
