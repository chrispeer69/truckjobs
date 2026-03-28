from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_branded_mail(subject, content_lines, recipient_email):
    """
    Wraps email content in an official HTML design with the logo.
    """
    # Build HTML Paragraphs
    paragraphs_html = "".join([f"<p style='margin-bottom: 16px; color: #374151;'>{p}</p>" for p in content_lines])
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Inter', -apple-system, sans-serif; background-color: #f3f4f6; margin: 0; padding: 40px 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="background-color: #ffffff; padding: 24px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                <img src="https://drivingjobs.online/static/images/logo.png" alt="DrivingJobs.online" style="height: 40px; width: auto;" onerror="this.outerHTML='<h2 style=\\'margin:0;color:#1e40af;\\'>DrivingJobs.online</h2>'">
            </div>
            <div style="padding: 32px 24px; font-size: 16px; line-height: 1.6;">
                <h3 style="margin-top: 0; color: #111827;">{subject}</h3>
                {paragraphs_html}
            </div>
            <div style="background-color: #f9fafb; padding: 20px 24px; text-align: center; font-size: 14px; color: #6b7280; border-top: 1px solid #e5e7eb;">
                &copy; {settings.DATE_FORMAT if hasattr(settings, 'DATE_FORMAT') else '2024'} DrivingJobs.online<br>
                <a href="https://drivingjobs.online/" style="color: #3b82f6; text-decoration: none;">Visit Website</a>
            </div>
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
