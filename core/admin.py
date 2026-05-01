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