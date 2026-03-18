from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_access_request_mail(dispatcher, driver):
    subject = f"Action Required: {dispatcher.company_name} requested access to your credentials"
    
    # We can create a quick html template later, or just send a nicely formatted text email for MVP
    message = (
        f"Hi {driver.user.first_name},\n\n"
        f"{dispatcher.company_name} is interested in your profile on TruckJobs and has requested "
        f"access to view your credential documents.\n\n"
        f"Log in to your dashboard to review and accept this request.\n\n"
        f"Thanks,\nThe TruckJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [driver.user.email],
        fail_silently=False,
    )

def send_access_granted_mail(driver, dispatcher):
    subject = f"Access Granted: {driver.user.get_full_name()}'s credentials are now available"
    
    message = (
        f"Hi {dispatcher.contact_name},\n\n"
        f"{driver.user.get_full_name()} has approved your request to view their credential documents.\n\n"
        f"You can now view their documents from your Dispatcher dashboard.\n\n"
        f"Thanks,\nThe TruckJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [dispatcher.user.email],
        fail_silently=False,
    )

def send_hire_mail(dispatcher, driver):
    subject = f"Congratulations! {dispatcher.company_name} wants to hire you"
    
    message = (
        f"Hi {driver.user.first_name},\n\n"
        f"Great news! {dispatcher.company_name} has officially indicated they want to hire you on TruckJobs.\n\n"
        f"They will be reaching out to you shortly using your contact information.\n\n"
        f"Thanks,\nThe TruckJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [driver.user.email],
        fail_silently=False,
    )

    
