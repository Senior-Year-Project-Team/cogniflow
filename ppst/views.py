from django.shortcuts import render

def index(request):
    """Main landing page for CogniFlow platform"""
    return render(request, "ppst/index.html")

def login(request):
    """Login page for clinicians and administrators"""
    return render(request, "ppst/login.html")

def patient_access(request):
    """Patient access page where they enter their unique test code"""
    return render(request, "ppst/patient_access.html")

def test_instructions(request):
    """Instructions page for patients before they start the test"""
    return render(request, "ppst/instructions.html")

def test_actual(request):
    """Actual test page where patients complete the cognitive test"""
    return render(request, "ppst/actual_test.html")

def clinician_dashboard(request):
    """Dashboard for clinicians to view patient results and manage tests"""
    return render(request, "ppst/clinician_dashboard.html")
