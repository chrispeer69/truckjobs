from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DriverProfile, Credential, DriverDocument
from companies.models import CredentialAccessRequest
from jobs.models import JobListing, JobApplication
from pools.models import CityPool
from core.emails import send_access_granted_mail


@login_required
def driver_profile(request):
    if request.user.role != 'driver':
        messages.error(request, 'This page is only for drivers.')
        return redirect('/')

    profile, created = DriverProfile.objects.get_or_create(user=request.user)

    tab = request.GET.get('tab', 'profile')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_profile':
            profile.cdl_class = request.POST.get('cdl_class', profile.cdl_class)
            
            try:
                profile.years_experience = int(request.POST.get('years_experience', 0) or 0)
            except ValueError:
                profile.years_experience = 0
                
            profile.specialties = request.POST.get('specialties', profile.specialties)
            profile.preferred_shift = request.POST.get('preferred_shift', profile.preferred_shift)
            profile.willing_relocate = request.POST.get('willing_relocate') == 'on'
            profile.bio = request.POST.get('bio', profile.bio)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.last_employer = request.POST.get('last_employer', profile.last_employer)
            profile.equipment_experience = request.POST.get('equipment_experience', profile.equipment_experience)

            profile.city = request.POST.get('city', profile.city)
            profile.state = (request.POST.get('state', profile.state) or '').upper()

            # Attempt to match a CityPool
            matched_pool = CityPool.objects.filter(
                name__iexact=profile.city, 
                state__iexact=profile.state, 
                is_active=True
            ).first()
            if matched_pool:
                profile.city_pool = matched_pool
            else:
                profile.city_pool = None
            
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('drivers:profile')

        elif action == 'update_passive':
            profile.availability = request.POST.get('availability', profile.availability)
            min_pay = request.POST.get('min_pay_hourly', '')
            if min_pay:
                profile.min_pay_hourly = float(min_pay)
            profile.save()
            messages.success(request, 'Passive talent settings updated!')
            return redirect('drivers:profile')

        elif action == 'update_alerts':
            profile.sms_profile_views = request.POST.get('sms_profile_views') == 'on'
            profile.sms_interview_req = request.POST.get('sms_interview_req') == 'on'
            profile.sms_private_offer = request.POST.get('sms_private_offer') == 'on'
            profile.sms_job_match = request.POST.get('sms_job_match') == 'on'
            profile.alert_cdl_expiry = request.POST.get('alert_cdl_expiry') == 'on'
            profile.alert_dot_expiry = request.POST.get('alert_dot_expiry') == 'on'
            profile.alert_mvr_annual = request.POST.get('alert_mvr_annual') == 'on'
            profile.alert_wreckmaster = request.POST.get('alert_wreckmaster') == 'on'
            profile.save()
            messages.success(request, 'Alert preferences updated!')
            return redirect('drivers:profile')

        elif action == 'upload_document':
            document_file = request.FILES.get('document_file')
            document_name = request.POST.get('document_name', 'Document')
            if document_file:
                DriverDocument.objects.create(
                    driver=profile,
                    file=document_file,
                    name=document_name
                )
                messages.success(request, 'Document uploaded successfully to your vault.')
            return redirect(reverse('drivers:profile') + '?tab=credentials')

        elif action == 'handle_access_request':
            request_id = request.POST.get('request_id')
            verdict = request.POST.get('verdict')
            access_req = CredentialAccessRequest.objects.filter(id=request_id, driver=profile).first()
            if access_req:
                access_req.status = verdict
                access_req.save()
                if verdict == 'approved':
                    messages.success(request, f'Access granted to {access_req.dispatcher.company_name}.')
                    send_access_granted_mail(profile, access_req.dispatcher)
                else:
                    messages.success(request, 'Access request rejected.')
            return redirect(reverse('drivers:profile') + '?tab=credentials')

        elif action == 'upload_credential':
            cred_type = request.POST.get('credential_type', '')
            cred_file = request.FILES.get('credential_file')
            expiry = request.POST.get('expiry_date')

            if cred_type and cred_file:
                cred, _ = Credential.objects.get_or_create(
                    driver=profile,
                    credential_type=cred_type
                )
                cred.file = cred_file
                cred.status = 'pending'
                if expiry:
                    cred.expiry_date = expiry
                cred.save()
                messages.success(request, f'{cred.get_credential_type_display()} uploaded — pending review.')
            else:
                messages.warning(request, 'No file selected for upload.')
            return redirect(reverse('drivers:profile') + '?tab=credentials')



        elif action == 'withdraw_app':
            from jobs.models import JobApplication
            app_id = request.POST.get('app_id')
            if app_id:
                application = get_object_or_404(JobApplication, pk=app_id, driver=profile)
                application.stage = 'withdrawn'
                application.save()
                messages.success(request, 'Application withdrawn.')
            return redirect(reverse('drivers:profile') + '?tab=applications')

        elif action == 'accept_invite':
            from jobs.models import JobApplication
            app_id = request.POST.get('app_id')
            if app_id:
                application = get_object_or_404(JobApplication, pk=app_id, driver=profile)
                if application.stage == 'invited':
                    application.stage = 'interview'
                    application.save()
                    messages.success(request, 'Invitation accepted! You are now in the interviewing stage.')
            return redirect(reverse('drivers:profile') + '?tab=applications')

        elif action == 'decline_invite':
            from jobs.models import JobApplication
            app_id = request.POST.get('app_id')
            if app_id:
                application = get_object_or_404(JobApplication, pk=app_id, driver=profile)
                if application.stage == 'invited':
                    application.stage = 'withdrawn'
                    application.save()
                    messages.success(request, 'Invitation declined.')
            return redirect(reverse('drivers:profile') + '?tab=applications')

        elif action == 'reply_question':
            from jobs.models import JobApplication, ApplicationMessage
            app_id = request.POST.get('app_id')
            content = request.POST.get('content')
            if app_id and content:
                application = get_object_or_404(JobApplication, pk=app_id, driver=profile)
                ApplicationMessage.objects.create(
                    application=application,
                    sender_is_company=False,
                    content=content
                )
                
                from core.emails import send_message_mail
                send_message_mail(request.user.get_full_name(), application.job.company.user, application, content)
                # If was invited, maybe auto-accept? No, user said "respond"
                # But typically responding implies starting the interview
                if application.stage == 'invited':
                    application.stage = 'interview'
                    application.save()
                messages.success(request, 'Message sent!')
            return redirect(reverse('drivers:profile') + '?tab=applications')

    # Build context
    credentials = []
    cred_types = ['cdl', 'dot_medical', 'mvr', 'drug_test', 'wreckmaster', 'hazmat']
    existing = {c.credential_type: c for c in profile.credentials.all()}
    for ct in cred_types:
        if ct in existing:
            credentials.append(existing[ct])
        else:
            credentials.append(Credential(driver=profile, credential_type=ct, status='missing'))

    reviews = profile.reviews.select_related('company').all()
    applications = profile.applications.select_related('job', 'job__company').all()
    documents = profile.documents.all()
    access_requests = profile.access_requests_received.select_related('dispatcher').all()

    context = {
        'profile': profile,
        'tab': tab,
        'credentials': credentials,
        'documents': documents,
        'access_requests': access_requests,
        'reviews': reviews,
        'applications': applications,
        'city_pools': CityPool.objects.filter(is_active=True),
    }
    return render(request, 'drivers/profile.html', context)


@login_required
def quick_apply(request, job_id):
    if request.user.role != 'driver':
        messages.error(request, 'Only drivers can apply to jobs.')
        return redirect('jobs:list')

    job = get_object_or_404(JobListing, pk=job_id, status='active')
    profile = request.user.driver_profile

    app, created = JobApplication.objects.get_or_create(
        job=job,
        driver=profile,
        defaults={'stage': 'applied'}
    )

    if created:
        messages.success(request, f'Applied to "{job.title}" successfully!')
    else:
        messages.info(request, f'You already applied to "{job.title}".')

    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/jobs/'))
    return redirect(next_url)


@login_required
def driver_profile_public(request, driver_id):
    driver = get_object_or_404(DriverProfile, pk=driver_id)
    reviews = driver.reviews.select_related('company').order_by('-created_at')
    return render(request, 'drivers/public_profile.html', {
        'driver': driver,
        'reviews': reviews
    })

@login_required
def leave_company_review(request, company_id):
    if request.method != 'POST' or request.user.role != 'driver':
        return redirect('/')

    from companies.models import CompanyProfile, CompanyReview
    from jobs.models import JobApplication

    company = get_object_or_404(CompanyProfile, pk=company_id)
    driver = request.user.driver_profile

    # SECURITY CHECK: Must be hired
    if not JobApplication.objects.filter(driver=driver, job__company=company, stage='hired').exists():
        messages.error(request, "You can only review companies that have hired you.")
        return redirect('drivers:profile')

    # One review per company per driver
    if CompanyReview.objects.filter(driver=driver, company=company).exists():
        messages.error(request, "You have already reviewed this company.")
        return redirect('drivers:profile')

    CompanyReview.objects.create(
        driver=driver,
        company=company,
        professionalism=int(request.POST.get('professionalism', 5)),
        communication=int(request.POST.get('communication', 5)),
        pay_reliability=int(request.POST.get('pay_reliability', 5)),
        equipment_quality=int(request.POST.get('equipment_quality', 5)),
        comment=request.POST.get('comment', '').strip()
    )
    
    messages.success(request, f"Review submitted for {company.company_name}!")
    return redirect(request.META.get('HTTP_REFERER', 'drivers:profile'))

