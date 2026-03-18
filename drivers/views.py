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
            profile.years_experience = int(request.POST.get('years_experience', profile.years_experience))
            profile.specialties = request.POST.get('specialties', profile.specialties)
            profile.preferred_shift = request.POST.get('preferred_shift', profile.preferred_shift)
            profile.willing_relocate = request.POST.get('willing_relocate') == 'on'
            profile.bio = request.POST.get('bio', profile.bio)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.city = request.POST.get('city', profile.city)
            profile.state = request.POST.get('state', profile.state).upper()
            profile.last_employer = request.POST.get('last_employer', profile.last_employer)
            profile.equipment_experience = request.POST.get('equipment_experience', profile.equipment_experience)

            # Update city pool
            city_pool = CityPool.objects.filter(
                name__iexact=profile.city,
                state__iexact=profile.state,
                is_active=True
            ).first()
            profile.city_pool = city_pool
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
            if cred_type:
                cred, _ = Credential.objects.get_or_create(
                    driver=profile,
                    credential_type=cred_type,
                    defaults={'status': 'pending'}
                )
                if cred.status == 'missing':
                    cred.status = 'pending'
                    cred.save()
                messages.success(request, f'Credential marked as uploaded — pending review.')
            return redirect(reverse('drivers:profile') + '?tab=credentials')

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
