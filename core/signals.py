from decouple import config
from django.db.models.signals import post_save
from django.dispatch import receiver
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .models import Invitation


API_SENDGRID = config("API_SENDGRID")
FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@example.com")
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")


@receiver(post_save, sender=Invitation)
def send_invitation_email(sender, instance, created, **kwargs):
    print("API_SENDGRID starts:", repr(API_SENDGRID[:10]))
    print("API_SENDGRID length:", len(API_SENDGRID))
    print("FROM_EMAIL:", repr(FROM_EMAIL))
    if not created:
        return

    if not API_SENDGRID:
        raise RuntimeError("Missing API_SENDGRID")

    invite_link = f"{SITE_URL}/accept-invite/{instance.token}/"

    subject = "Create your Rounders account"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#111827;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;">
          
          <tr>
            <td style="background:#dc2626;padding:28px 32px;color:#ffffff;">
              <div style="font-size:24px;font-weight:700;letter-spacing:-0.3px;">Rounders</div>
              <div style="font-size:14px;margin-top:6px;opacity:0.9;">Scheduling intelligence for CPA firms</div>
            </td>
          </tr>

          <tr>
            <td style="padding:36px 32px;">
              <h1 style="margin:0 0 16px;font-size:24px;line-height:1.25;color:#111827;">
                Create your Rounders account
              </h1>

              <p style="margin:0 0 18px;font-size:16px;line-height:1.6;color:#374151;">
                You’ve been invited to join <strong>{instance.company.practice_name}</strong> on Rounders.
              </p>

              <p style="margin:0 0 28px;font-size:16px;line-height:1.6;color:#374151;">
                Confirm your email and create your username and password to access your firm’s account.
              </p>

              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#dc2626;border-radius:10px;">
                    <a href="{invite_link}" 
                       style="display:inline-block;padding:14px 22px;font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;">
                      Create Account
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:28px 0 0;font-size:13px;line-height:1.6;color:#6b7280;">
                If the button doesn’t work, copy and paste this link into your browser:
              </p>

              <p style="margin:8px 0 0;font-size:13px;line-height:1.6;word-break:break-all;">
                <a href="{invite_link}" style="color:#dc2626;text-decoration:underline;">{invite_link}</a>
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding:22px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;line-height:1.6;color:#6b7280;">
                If you didn’t expect this invitation, you can safely ignore this email.
              </p>
              <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">
                © Rounders
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
    </body>
    </html>
    """

    sg = SendGridAPIClient(API_SENDGRID)
    msg = Mail(
        from_email=FROM_EMAIL,
        to_emails=instance.email,
        subject=subject,
        html_content=html,
    )

    resp = sg.send(msg)

    if not (200 <= resp.status_code < 300):
        raise RuntimeError(f"SendGrid failed: {resp.status_code} {resp.body}")