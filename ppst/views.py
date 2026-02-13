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
