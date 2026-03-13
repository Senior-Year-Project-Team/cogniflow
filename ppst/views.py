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
    # DEMO ONLY: Fake data for dashboard preview (safe to delete)
    recent_results = [
        {
            "patient_id": "P-0001",
            "age_bracket": "65–74",
            "avg_latency_ms": 1234,
            "correct_percent": 92,
            "export_url": example_export_url,
        },
        {
            "patient_id": "P-0002",
            "age_bracket": "55–64",
            "avg_latency_ms": 1480,
            "correct_percent": 88,
            "export_url": example_export_url,
        },
        {
            "patient_id": "P-0003",
            "age_bracket": "75–84",
            "avg_latency_ms": 1715,
            "correct_percent": 81,
            "export_url": example_export_url,
        },
        # DEMO ONLY: Fake completed test entry (safe to delete)
        {
            "patient_id": "P-TEST-0004",
            "age_bracket": "65–74",
            "avg_latency_ms": 1395,
            "correct_percent": 94,
            "export_url": example_export_url,
        },
    ]
    context = {
        "total_tests":          4,
        "mean_correct_percent": 89,
        "mean_latency_ms":      1456,
        "age_bracket_count":    3,
        "recent_results":       recent_results,
        "is_test_giver":        True,
        "patient_access_link":  request.build_absolute_uri("/patient-access/"),
    }
    return render(request, "ppst/clinician_dashboard.html", context)


def export_test_example(request):
    """Return a small CSV file as an example per-patient export."""
    content = (
        "patient_id,age_bracket,trial_number,trial_type,stimulus,span,click_latencies_ms,avg_latency_ms,correct_percent\n"
        "P-0001,65-74,1,digit,\"7 3 1 8\",4,\"520 1320 2220 3090\",1476,87\n"
        "P-0001,65-74,2,digit,\"4 1 9 6\",4,\"540 1360 2280 3150\",1476,87\n"
        "P-0001,65-74,3,digit,\"5 8 2 7 3\",5,\"610 1550 2550 3490 4680\",1476,87\n"
        "P-0001,65-74,4,digit,\"9 4 6 1 8\",5,\"640 1510 2380 3260 4180\",1476,87\n"
        "P-0001,65-74,5,digit,\"3 7 2 9\",4,\"560 1410 2290 3180\",1476,87\n"
        "P-0001,65-74,6,digit,\"1 5 4 8 6\",5,\"650 1540 2460 3380 4260\",1476,87\n"
        "P-0001,65-74,7,mixed,\"A 3 K 5\",4,\"590 1400 2330 3180\",1476,87\n"
        "P-0001,65-74,8,mixed,\"5 R 2 B 7\",5,\"620 1580 2520 3440 4620\",1476,87\n"
        "P-0001,65-74,9,mixed,\"T 7 D 4\",4,\"580 1390 2260 3120\",1476,87\n"
        "P-0001,65-74,10,mixed,\"9 L 3 F 6\",5,\"610 1550 2550 3490 4680\",1476,87\n"
        "P-0001,65-74,11,mixed,\"M 2 S 8\",4,\"570 1370 2240 3100\",1476,87\n"
        "P-0001,65-74,12,mixed,\"4 R 1 E 7\",5,\"600 1500 2440 3360 4550\",1476,87\n"
    )
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ppst_example_result.csv"'
    return response
