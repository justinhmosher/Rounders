from django.contrib import admin
from .models import Company, Invitation, Profile


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("practice_name", "company_id", "created_at")
    search_fields = ("practice_name", "company_id")
    ordering = ("practice_name",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "company", "role", "accepted", "expires_at", "created_at")
    list_filter = ("role", "accepted", "company")
    search_fields = ("email", "company__practice_name", "company__company_id")
    readonly_fields = ("token", "created_at")
    ordering = ("-created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "company", "role", "created_at")
    list_filter = ("role", "company")
    search_fields = (
        "user__username",
        "user__email",
        "company__practice_name",
        "company__company_id",
    )
    ordering = ("company", "user__username")

    def email(self, obj):
        return obj.user.email

from .models import (
    Client,
    FederalReturnType,
    FederalDueDateRule,
    TaxReturnProject,
)


class FederalDueDateRuleInline(admin.TabularInline):
    model = FederalDueDateRule
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "client_type",
        "primary_contact_name",
        "email",
        "phone",
        "active",
        "created_at",
    )

    list_filter = (
        "client_type",
        "active",
        "created_at",
    )

    search_fields = (
        "name",
        "primary_contact_name",
        "email",
        "phone",
        "external_client_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(FederalReturnType)
class FederalReturnTypeAdmin(admin.ModelAdmin):
    list_display = (
        "form_number",
        "name",
        "category",
        "frequency",
        "default_estimated_hours",
        "default_complexity",
        "requires_review",
        "active",
    )

    list_filter = (
        "category",
        "frequency",
        "default_complexity",
        "requires_review",
        "active",
    )

    search_fields = (
        "form_number",
        "name",
        "produced_when",
        "notes",
    )

    ordering = (
        "category",
        "form_number",
    )

    inlines = [
        FederalDueDateRuleInline,
    ]


@admin.register(FederalDueDateRule)
class FederalDueDateRuleAdmin(admin.ModelAdmin):
    list_display = (
        "return_type",
        "rule_type",
        "applies_to_period",
        "due_month",
        "due_day",
        "extension_month",
        "extension_day",
        "active",
    )

    list_filter = (
        "rule_type",
        "applies_to_period",
        "weekend_holiday_adjustment",
        "active",
    )

    search_fields = (
        "return_type__form_number",
        "return_type__name",
        "description",
    )

    autocomplete_fields = (
        "return_type",
    )


@admin.register(TaxReturnProject)
class TaxReturnProjectAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "return_type",
        "tax_year",
        "document_status",
        "work_status",
        "estimated_hours",
        "complexity",
        "manager_priority_override",
        "due_date",
        "extended_due_date",
        "extension_filed",
        "assigned_preparer",
        "assigned_reviewer",
        "scheduled_start_date",
        "scheduled_end_date",
        "active",
    )

    list_filter = (
        "tax_year",
        "document_status",
        "work_status",
        "complexity",
        "manager_priority_override",
        "extension_filed",
        "active",
        "return_type__category",
        "return_type__frequency",
    )

    search_fields = (
        "client__name",
        "return_type__form_number",
        "return_type__name",
        "internal_notes",
        "client_notes",
    )

    autocomplete_fields = (
        "client",
        "return_type",
        "due_date_rule",
        "assigned_preparer",
        "assigned_reviewer",
    )

    readonly_fields = (
        "priority_score",
        "due_date",
        "extended_due_date",
        "created_at",
        "updated_at",
    )

    ordering = (
        "due_date",
        "-priority_score",
        "client__name",
    )