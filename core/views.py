from cutwork import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
import re
from .models import Invitation, Profile, Client, FederalReturnType, TaxReturnProject
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

def manager(request):
    return render(request, "core/manager.html")


import json
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages

from .models import (
    Client,
    FederalReturnType,
    FederalDueDateRule,
    TaxReturnProject,
    FEDERAL_RETURN_TYPES,
    FEDERAL_DUE_DATE_RULES,
)


def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_decimal(value):
    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_int_or_none(value):
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def seed_federal_catalog_if_empty():
    """
    This does NOT change your models.
    It only makes sure your FederalReturnType database table has rows,
    because the dropdown pulls from the database.
    """

    if FederalReturnType.objects.exists():
        return

    for item in FEDERAL_RETURN_TYPES:
        FederalReturnType.objects.update_or_create(
            form_number=item["form_number"],
            defaults={
                "name": item["name"],
                "category": item["category"],
                "frequency": item["frequency"],
                "produced_when": item.get("produced_when", ""),
                "active": True,
            }
        )

    for rule in FEDERAL_DUE_DATE_RULES:
        return_type = FederalReturnType.objects.filter(
            form_number=rule["form_number"]
        ).first()

        if not return_type:
            continue

        FederalDueDateRule.objects.get_or_create(
            return_type=return_type,
            rule_type=rule["rule_type"],
            applies_to_period=rule.get("applies_to_period", ""),
            description=rule.get("description", ""),
            defaults={
                "due_month": rule.get("due_month"),
                "due_day": rule.get("due_day"),
                "extension_month": rule.get("extension_month"),
                "extension_day": rule.get("extension_day"),
                "months_after_period_end": rule.get("months_after_period_end"),
                "due_day_after_period_end": rule.get("due_day_after_period_end"),
                "active": True,
            }
        )


def get_allowed_categories_for_client_type(client_type):
    """
    Maps your Client.client_type to your FederalReturnType.category values.
    """

    category_map = {
        "individual": [
            "individual",
            "estimated_tax",
            "estate_gift",
            "information",
            "international",
        ],

        "business": [
            "business",
            "partnership",
            "corporation",
            "s_corporation",
            "employment",
            "information",
            "excise",
            "estimated_tax",
            "withholding",
            "international",
            "retirement",
            "other",
        ],

        "trust_estate": [
            "trust_estate",
            "estate_gift",
            "estimated_tax",
            "information",
            "international",
        ],

        "nonprofit": [
            "exempt_org",
            "information",
            "employment",
            "excise",
            "other",
        ],

        "other": [
            "individual",
            "business",
            "partnership",
            "corporation",
            "s_corporation",
            "trust_estate",
            "exempt_org",
            "estate_gift",
            "employment",
            "information",
            "excise",
            "international",
            "retirement",
            "estimated_tax",
            "withholding",
            "other",
        ],
    }

    return category_map.get(client_type, category_map["other"])


# @login_required
def create_client_project(request):
    seed_federal_catalog_if_empty()

    return_types = FederalReturnType.objects.filter(active=True).order_by(
        "category",
        "form_number"
    )

    return_types_json = []

    for return_type in return_types:
        return_types_json.append({
            "id": return_type.id,
            "form_number": return_type.form_number,
            "name": return_type.name,
            "category": return_type.category,
            "frequency": return_type.frequency,
            "produced_when": return_type.produced_when or "",
            "default_estimated_hours": str(return_type.default_estimated_hours or ""),
            "default_complexity": return_type.default_complexity or "medium",
            "requires_review": return_type.requires_review,
        })

    if request.method == "POST":
        client_name = request.POST.get("client_name", "").strip()
        client_type = request.POST.get("client_type", "individual")

        primary_contact_name = request.POST.get("primary_contact_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()

        client_notes = request.POST.get("client_notes", "").strip()

        fiscal_year_end_month = parse_int_or_none(
            request.POST.get("fiscal_year_end_month")
        )
        fiscal_year_end_day = parse_int_or_none(
            request.POST.get("fiscal_year_end_day")
        )

        return_type_id = request.POST.get("return_type")
        tax_year = request.POST.get("tax_year")

        period_start_date = parse_date(request.POST.get("period_start_date"))
        period_end_date = parse_date(request.POST.get("period_end_date"))
        docs_received_date = parse_date(request.POST.get("docs_received_date"))

        document_status = request.POST.get("document_status", "no_docs")
        work_status = request.POST.get("work_status", "not_started")
        estimated_hours = parse_decimal(request.POST.get("estimated_hours"))
        complexity = request.POST.get("complexity", "medium")
        manager_priority_override = request.POST.get(
            "manager_priority_override",
            "normal"
        )
        extension_filed = request.POST.get("extension_filed") == "on"

        internal_notes = request.POST.get("internal_notes", "").strip()

        if not client_name:
            messages.error(request, "Client name is required.")
            return redirect("create_client_project")

        if not return_type_id:
            messages.error(request, "Return type is required.")
            return redirect("create_client_project")

        try:
            tax_year = int(tax_year)
        except (TypeError, ValueError):
            messages.error(request, "Tax year is required and must be valid.")
            return redirect("create_client_project")

        if fiscal_year_end_month and not 1 <= fiscal_year_end_month <= 12:
            messages.error(request, "Fiscal year end month must be between 1 and 12.")
            return redirect("create_client_project")

        if fiscal_year_end_day and not 1 <= fiscal_year_end_day <= 31:
            messages.error(request, "Fiscal year end day must be between 1 and 31.")
            return redirect("create_client_project")

        try:
            return_type = FederalReturnType.objects.get(
                id=return_type_id,
                active=True
            )
        except FederalReturnType.DoesNotExist:
            messages.error(request, "Invalid return type selected.")
            return redirect("create_client_project")

        allowed_categories = get_allowed_categories_for_client_type(client_type)

        if return_type.category not in allowed_categories:
            messages.error(
                request,
                "That return type does not match the selected client type."
            )
            return redirect("/manager/create-client-project/")

        client = Client.objects.create(
            name=client_name,
            client_type=client_type,
            external_client_id="",
            primary_contact_name=primary_contact_name,
            email=email,
            phone=phone,
            fiscal_year_end_month=fiscal_year_end_month,
            fiscal_year_end_day=fiscal_year_end_day,
            notes=client_notes,
        )

        project = TaxReturnProject.objects.create(
            client=client,
            return_type=return_type,
            tax_year=tax_year,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            extension_filed=extension_filed,
            document_status=document_status,
            docs_received_date=docs_received_date,
            work_status=work_status,
            estimated_hours=estimated_hours,
            actual_hours=None,
            complexity=complexity,
            manager_priority_override=manager_priority_override,
            internal_notes=internal_notes,
            client_notes="",
        )

        messages.success(
            request,
            f"Created project: {project.client.name} - {project.return_type.form_number} - {project.tax_year}"
        )

        return redirect("/manager/create-client-project/")

    context = {
        "return_types": return_types,
        "return_types_json": return_types_json,
        "client_type_choices": Client.CLIENT_TYPE_CHOICES,
        "document_status_choices": TaxReturnProject.DOCUMENT_STATUS_CHOICES,
        "work_status_choices": TaxReturnProject.WORK_STATUS_CHOICES,
        "complexity_choices": TaxReturnProject.COMPLEXITY_CHOICES,
        "priority_choices": TaxReturnProject.PRIORITY_CHOICES,
    }

    return render(request, "core/create_client_project.html", context)