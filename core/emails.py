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

def send_password_reset_otp(user, otp_code):
    subject = "Your Password Reset Code"
    
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"You requested to reset your password on DrivingJobs.online.\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code will expire in 15 minutes.\n\n"
        f"If you did not request a password reset, you can safely ignore this email.\n\n"
        f"Thanks,\nThe DrivingJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_message_mail(sender_name, recipient, application, content=None):
    subject = f"New Message from {sender_name}"
    
    message = (
        f"Hi {recipient.first_name or recipient.username},\n\n"
        f"You have a new message from {sender_name} regarding the application for '{application.job.title}'.\n\n"
    )
    if content:
        message += f"\"{content}\"\n\n"
        
    message += (
        f"Log in to your dashboard to reply.\n\n"
        f"Thanks,\nThe TruckJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        fail_silently=False,
    )

def send_job_match_mail(driver, job):
    subject = f"New Job Match: {job.title} in {job.location}"
    
    message = (
        f"Hi {driver.user.first_name or driver.user.username},\n\n"
        f"We found a new job that matches your profile!\n\n"
        f"Job: {job.title}\n"
        f"Company: {job.company.company_name}\n"
        f"Location: {job.location}\n\n"
        f"Log in to your TruckJobs dashboard to review and apply.\n\n"
        f"Thanks,\nThe TruckJobs Team"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [driver.user.email],
        fail_silently=False,
    )
