from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime

def send_branded_mail(subject, content_lines, recipient_email):
    """
    Wraps email content in an official HTML design with the logo.
    """
    # Build HTML Paragraphs
    paragraphs_html = "".join([f"<p style='margin-bottom: 16px; color: #374151;'>{p}</p>" for p in content_lines])
    
    current_year = datetime.date.today().year
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&family=Barlow+Condensed:wght@700;800&display=swap');
            body {{ font-family: 'Barlow', sans-serif !important; }}
            .brand {{ color: #D85A30; }}
            .text-dark {{ color: #1A1A18; }}
        </style>
    </head>
    <body style="font-family: 'Barlow', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FAFAF8; margin: 0; padding: 40px 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #E2E0D8; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            <!-- Header -->
            <div style="background-color: #ffffff; padding: 24px; text-align: center; border-bottom: 2px solid #D85A30; border-top: 1px solid #E2E0D8;">
                <a href="https://drivingjobs.online/" style="text-decoration: none; display: inline-block;">
                    <div style="font-family: 'Barlow Condensed', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 800; font-size: 24px; text-transform: none; line-height: 1;">
                        <span style="color: #D85A30; font-weight: 800;">driving</span><span style="color: #000000; font-weight: 800;">jobs.online</span>
                    </div>
                </a>
            </div>
            
            <div style="padding: 40px 32px; color: #1A1A18;">
                <h2 style="margin-top: 0; color: #1A1A18; font-family: 'Barlow Condensed', sans-serif; font-size: 28px; font-weight: 800; line-height: 1.1; margin-bottom: 24px;">{subject}</h2>
                <div style="font-size: 16px; line-height: 1.6; color: #5F5E5A;">
                    {paragraphs_html}
                </div>
            </div>
            
            <div style="background-color: #F4F3EF; padding: 32px; text-align: center; border-top: 1px solid #E2E0D8;">
                <p style="margin: 0; font-size: 14px; color: #888780; margin-bottom: 16px;">
                    &copy; {current_year} DrivingJobs.online. All rights reserved.
                </p>
                <div style="margin-bottom: 20px;">
                    <a href="https://drivingjobs.online/" style="display: inline-block; padding: 12px 24px; background-color: #D85A30; border-radius: 8px; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; transition: background 0.2s;">Visit Website</a>
                </div>
                <p style="margin: 0; font-size: 12px; color: #888780;">
                    You are receiving this because you registered on DrivingJobs.online
                </p>
            </div>
        </div>
        <div style="text-align: center; margin-top: 24px; font-size: 12px; color: #888780;">
            Sent by the DrivingJobs Team
        </div>
    </body>
    </html>
    """
    
    plain_message = "\n\n".join(content_lines) + "\n\nhttps://drivingjobs.online/"
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
        html_message=html_message
    )


def send_access_request_mail(dispatcher, driver, credential_name="credential"):
    subject = f"Action Required: {dispatcher.company_name} requested access to your {credential_name}"
    content = [
        f"Hi {driver.user.first_name},",
        f"{dispatcher.company_name} is interested in your profile on DrivingJobs.online and has requested access to view your {credential_name} document.",
        "Log in to your dashboard to review and accept this request.",
        "Thanks,<br>The DrivingJobs Team"
    ]
    send_branded_mail(subject, content, driver.user.email)

def send_access_granted_mail(driver, dispatcher):
    subject = f"Access Granted: {driver.user.get_full_name()}'s credentials are now available"
    content = [
        f"Hi {dispatcher.contact_name},",
        f"{driver.user.get_full_name()} has approved your request to view their credential documents.",
        "You can now securely view their documents directly from your Dispatcher dashboard.",
        "Thanks,<br>The DrivingJobs Team"
    ]
    send_branded_mail(subject, content, dispatcher.user.email)

def send_hire_mail(dispatcher, driver):
    subject = f"Congratulations! {dispatcher.company_name} wants to hire you"
    content = [
        f"Hi {driver.user.first_name},",
        f"Great news! {dispatcher.company_name} has officially indicated they want to hire you on DrivingJobs.online.",
        "They will be reaching out to you shortly using your contact information.",
        "Thanks,<br>The DrivingJobs Team"
    ]
    send_branded_mail(subject, content, driver.user.email)

def send_password_reset_otp(user, otp_code):
    subject = "Your Password Reset Code"
    content = [
        f"Hi {user.first_name or user.username},",
        "You requested to reset your password on DrivingJobs.online.",
        f"Your verification code is: <strong>{otp_code}</strong>",
        "This code will expire in 15 minutes.",
        "If you did not request a password reset, you can safely ignore this email.",
        "Thanks,<br>The DrivingJobs Team"
    ]
    send_branded_mail(subject, content, user.email)

def send_message_mail(sender_name, recipient, application, content=None):
    subject = f"New Message from {sender_name}"
    email_content = [
        f"Hi {recipient.first_name or recipient.username},",
        f"You have a new message from {sender_name} regarding the application for '{application.job.title}'."
    ]
    if content:
        email_content.append(f"<blockquote style='border-left: 4px solid #e5e7eb; padding-left: 16px; margin-left: 0; color: #4b5563; font-style: italic;'>\"{content}\"</blockquote>")
        
    email_content.append("Log in to your dashboard to reply.")
    email_content.append("Thanks,<br>The DrivingJobs Team")
    
    send_branded_mail(subject, email_content, recipient.email)

def send_job_match_mail(driver, job):
    subject = f"New Job Match: {job.title} in {job.location}"
    content = [
        f"Hi {driver.user.first_name or driver.user.username},",
        "We found a new job that matches your profile!",
        f"<strong>Job:</strong> {job.title}<br><strong>Company:</strong> {job.company.company_name}<br><strong>Location:</strong> {job.location}",
        "Log in to your DrivingJobs dashboard to review and apply.",
        "Thanks,<br>The DrivingJobs Team"
    ]
    send_branded_mail(subject, content, driver.user.email)
