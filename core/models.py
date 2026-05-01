from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class Company(models.Model):
    practice_name = models.CharField(max_length=255)
    company_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.practice_name}"


class Invitation(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    email = models.EmailField()
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invitations"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.expires_at is not None and timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} invited to {self.company.practice_name} as {self.role}"


class Profile(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="profiles"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.practice_name} - {self.role}"