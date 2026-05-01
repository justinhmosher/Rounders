from cutwork import settings
from django.shortcuts import render

def home(request):
    return render(request, "core/home.html")

def signin(request):
    return render(request, "core/signin.html")
