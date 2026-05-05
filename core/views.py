from cutwork import settings
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
import re
from .models import Invitation, Profile

def home(request):
    return render(request, "core/home.html")

def signin(request):
    return render(request, "core/signin.html")

def is_strong_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"\d", password)
        and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )


def owner_signup(request, token):
    invitation = get_object_or_404(Invitation, token=token)

    if invitation.accepted:
        return render(request, "core/invite_invalid.html", {
            "message": "This invitation has already been used."
        })

    if invitation.expires_at and timezone.now() > invitation.expires_at:
        return render(request, "core/invite_invalid.html", {
            "message": "This invitation has expired."
        })

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not password or not confirm_password:
            return JsonResponse({
                "success": False,
                "message": "Please complete all fields."
            }, status=400)

        if password != confirm_password:
            return JsonResponse({
                "success": False,
                "message": "Passwords do not match."
            }, status=400)

        if not is_strong_password(password):
            return JsonResponse({
                "success": False,
                "message": "Password must be at least 8 characters and include an uppercase letter, number, and special character."
            }, status=400)

        if len(username) < 8:
            return JsonResponse({
                "success": False,
                "message": "Username must be at least 8 characters long."
            }, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "success": False,
                "message": "That username is already taken."
            }, status=400)

        if User.objects.filter(email=invitation.email).exists():
            return JsonResponse({
                "success": False,
                "message": "An account with this email already exists."
            }, status=400)

        user = User.objects.create_user(
            username=username,
            email=invitation.email,
            password=password,
        )

        Profile.objects.create(
            user=user,
            company=invitation.company,
            role=invitation.role,
        )

        invitation.accepted = True
        invitation.save()

        login(request, user)

        return JsonResponse({
            "success": True,
            "message": "Account created successfully.",
            "redirect_url": "/dashboard/"
        })

    return render(request, "core/signup.html", {
        "invitation": invitation
    })

def staff(request):
    return render(request, "core/staff.html")
