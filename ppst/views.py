from django.shortcuts import render, redirect

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
    context = {
        "total_tests":          0,
        "mean_correct_percent": 0,
        "mean_latency_ms":      0,
        "age_bracket_count":    0,
        "recent_results":       [],
        "is_test_giver":        True,
        "patient_access_link":  request.build_absolute_uri("/patient-access/"),
    }
    return render(request, "ppst/clinician_dashboard.html", context)
