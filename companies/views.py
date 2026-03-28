import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import CompanyProfile, CredentialAccessRequest
from jobs.models import JobListing, JobApplication
from drivers.models import DriverProfile, Credential
from core.emails import send_access_request_mail


@login_required
def dashboard(request):
    if request.user.role != 'company':
        messages.error(request, 'This page is only for companies.')
        return redirect('/')

    profile = request.user.company_profile
    tab = request.GET.get('tab', 'jobs')

    # My Jobs data
    from django.db.models import Count
    company_jobs = profile.job_listings.annotate(applicant_count=Count('applications')).order_by('-created_at')
    applications = JobApplication.objects.filter(job__company=profile).select_related('driver', 'driver__user', 'job')

    # City Pool
    pool_drivers = []
    if profile.city_pool:
        pool_drivers = list(DriverProfile.objects.filter(
            city_pool=profile.city_pool, is_active=True
        ).select_related('user'))

    # Access Requests — attach to each pool driver for template use
    access_requests = CredentialAccessRequest.objects.filter(dispatcher=profile)
    request_map = {req.driver_id: req for req in access_requests}

    for driver in pool_drivers:
        driver.access_request = request_map.get(driver.id)

    # Handle POST actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile.company_name = request.POST.get('company_name', profile.company_name)
            profile.company_type = request.POST.get('company_type', profile.company_type)
            profile.contact_name = request.POST.get('contact_name', profile.contact_name)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.contact_method = request.POST.get('contact_method', profile.contact_method)
            
            try:
                profile.years_in_operation = int(request.POST.get('years_in_operation', 0) or 0)
            except ValueError:
                profile.years_in_operation = 0
                
            profile.city = request.POST.get('city', profile.city)
            profile.state = (request.POST.get('state', profile.state) or '').upper()

            # Attempt to match a CityPool
            from pools.models import CityPool
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
            return redirect('/company/dashboard/?tab=profile')
            
        elif action == 'request_credentials':
            driver_id = request.POST.get('driver_id')
            driver_target = get_object_or_404(DriverProfile, pk=driver_id)
            req, created = CredentialAccessRequest.objects.get_or_create(
                dispatcher=profile,
                driver=driver_target,
                defaults={'status': 'pending'}
            )
            if created:
                send_access_request_mail(profile, driver_target)
                messages.success(request, f'Access requested from {driver_target.user.get_full_name()}.')
            return redirect('/company/dashboard/?tab=pool')

    # Credential alerts
    cred_alerts = []
    hired_or_applied_driver_ids = applications.values_list('driver_id', flat=True).distinct()
    if hired_or_applied_driver_ids:
        soon = timezone.now().date() + timedelta(days=60)
        cred_alerts = Credential.objects.filter(
            driver_id__in=hired_or_applied_driver_ids,
            expiry_date__isnull=False,
            expiry_date__lte=soon,
        ).exclude(status='missing').select_related('driver', 'driver__user').order_by('expiry_date')

    # Pipeline kanban grouping (REMOVED - now per job in job_kanban view)

    context = {
        'profile': profile,
        'tab': tab,
        'company_jobs': company_jobs,
        'pool_drivers': pool_drivers,
        'cred_alerts': cred_alerts,
        'request_map': request_map,
        'stats': {
            'open_positions': company_jobs.filter(status='active').count(),
            'total_applicants': applications.count(),
            'interviews_this_week': applications.filter(
                stage='interview',
                updated_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
    }
    return render(request, 'companies/dashboard.html', context)


@login_required
def post_job(request):
    if request.user.role != 'company':
        messages.error(request, 'This page is only for companies.')
        return redirect('/')

    profile = request.user.company_profile

    if request.method == 'POST':
        benefits_list = request.POST.getlist('benefits')
        status = 'draft' if request.POST.get('save_draft') else 'active'

        job = JobListing.objects.create(
            company=profile,
            city_pool=profile.city_pool,
            title=request.POST.get('title', ''),
            category=request.POST.get('category', 'tow_truck'),
            employment_type=request.POST.get('employment_type', 'full_time'),
            cdl_requirement=request.POST.get('cdl_requirement', 'no_cdl'),
            experience_years=int(request.POST.get('experience_years', 0)),
            pay_min=float(request.POST.get('pay_min', 0)) if request.POST.get('pay_min') else None,
            pay_max=float(request.POST.get('pay_max', 0)) if request.POST.get('pay_max') else None,
            pay_type=request.POST.get('pay_type', 'hourly'),
            description=request.POST.get('description', ''),
            benefits=json.dumps(benefits_list) if benefits_list else '[]',
            is_urgent=request.POST.get('is_urgent') == 'on',
            status=status,
        )

        if status == 'draft':
            messages.success(request, 'Job saved as draft.')
        else:
            # Trigger Job Match Emails
            if job.city_pool:
                matching_drivers = job.city_pool.driverprofile_set.filter(
                    is_active=True,
                    cdl_class=job.cdl_requirement
                )
                from core.emails import send_job_match_mail
                for driver in matching_drivers:
                    if driver.sms_job_match: # Respect user alert settings
                        send_job_match_mail(driver, job)
                        
            messages.success(request, f'"{job.title}" is now live! Drivers in your city pool can see it.')
        return redirect('companies:company_jobs')

    all_benefits = [
        'Health insurance', 'Dental/vision', '401k', 'Sign-on bonus',
        'Paid time off', 'Overtime available', 'Take-home truck', 'Fuel card',
        'Uniforms provided', 'Weekly pay', 'Daily pay option', 'Dispatch bonus',
    ]

    return render(request, 'companies/post_job.html', {
        'profile': profile,
        'all_benefits': all_benefits,
    })


@login_required
def company_jobs(request):
    if request.user.role != 'company':
        return redirect('/')
    profile = request.user.company_profile
    jobs = profile.job_listings.all()
    return render(request, 'companies/company_jobs.html', {'jobs': jobs, 'profile': profile})


@login_required
def update_stage(request, app_id):
    if request.method != 'POST':
        return redirect('/company/dashboard/')

    if request.user.role != 'company':
        messages.error(request, 'Not authorized.')
        return redirect('/')

    application = get_object_or_404(JobApplication, pk=app_id, job__company=request.user.company_profile)
    action = request.POST.get('action')
    new_stage = request.POST.get('stage')

    if action == 'ask_question':
        content = request.POST.get('content', '').strip()
        if content:
            from jobs.models import ApplicationMessage
            from core.emails import send_message_mail
            
            # Anti-spam checks
            last_msgs = ApplicationMessage.objects.filter(application=application).order_by('-created_at')[:2]
            if len(last_msgs) == 2 and all(m.sender_is_company for m in last_msgs):
                messages.error(request, 'You cannot send more than 2 consecutive messages until the driver replies.')
                return redirect(f'/company/job/{application.job.pk}/dashboard/')
            
            if len(content) > 300:
                messages.error(request, 'Message must be 300 characters or less.')
                return redirect(f'/company/job/{application.job.pk}/dashboard/')
            
            ApplicationMessage.objects.create(
                application=application,
                sender_is_company=True,
                content=content
            )
            
            # Send Notification Email
            send_message_mail(request.user.company_profile.company_name, application.driver.user, application, content)
            
            # Move to interview stage if they asked a question
            if application.stage in ['applied', 'reviewed', 'invited']:
                application.stage = 'interview'
            application.save()
            messages.success(request, f'Question sent to {application.driver.user.get_full_name()}.')
    
    elif action == 'request_credentials':
        credential_type = request.POST.get('credential_type')
        if not credential_type:
            messages.error(request, 'Please select a credential type.')
            return redirect(f'/company/job/{application.job.pk}/dashboard/')

        # Create a pending access request natively scoped to the specific type
        req, created = CredentialAccessRequest.objects.get_or_create(
            dispatcher=request.user.company_profile,
            driver=application.driver,
            credential_type=credential_type,
            defaults={'status': 'pending'}
        )
        if created:
            send_access_request_mail(request.user.company_profile, application.driver, dict(Credential.TYPE_CHOICES).get(credential_type, "credential").lower())
        elif req.status == 'rejected':
            req.status = 'pending'
            req.save()
            send_access_request_mail(request.user.company_profile, application.driver, dict(Credential.TYPE_CHOICES).get(credential_type, "credential").lower())
        
        if application.stage in ['applied', 'reviewed']:
                application.stage = 'interview'
        application.save()
        messages.success(request, f'{dict(Credential.TYPE_CHOICES).get(credential_type, "Credential")} access requested from {application.driver.user.get_full_name()}.')
        
    elif new_stage in dict(JobApplication.STAGE_CHOICES):
        application.stage = new_stage
        application.save()
        messages.success(request, f'Application moved to {application.get_stage_display()}.')
        
        if new_stage == 'hired':
            from core.emails import send_hire_mail
            send_hire_mail(request.user.company_profile, application.driver)

    return redirect(f'/company/job/{application.job.pk}/dashboard/')


@login_required
def job_dashboard(request, job_id):
    if request.user.role != 'company':
        messages.error(request, 'This page is only for companies.')
        return redirect('/')
        
    profile = request.user.company_profile
    job = get_object_or_404(JobListing, pk=job_id, company=profile)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'invite':
            driver_id = request.POST.get('driver_id')
            driver = get_object_or_404(DriverProfile, pk=driver_id)
            app, created = JobApplication.objects.get_or_create(
                job=job,
                driver=driver,
                defaults={'stage': 'invited'}
            )
            if app.stage in ['withdrawn', 'rejected']:
                app.stage = 'invited'
                app.save()
            messages.success(request, f'Invited {driver.user.get_full_name()} to apply for this job.')
            return redirect('companies:job_dashboard', job_id=job.pk)
            
    applications = JobApplication.objects.filter(job=job).select_related('driver', 'driver__user')
    
    # Pool drivers for Search tab
    pool_drivers = []
    if job.city_pool:
        applied_driver_ids = applications.values_list('driver_id', flat=True)
        pool_drivers = DriverProfile.objects.filter(
            city_pool=job.city_pool, is_active=True
        ).exclude(id__in=applied_driver_ids)

    pipeline = {
        'search': pool_drivers,
        'candidates': applications.filter(stage__in=['applied', 'reviewed', 'invited']),
        'interviewing': applications.filter(stage='interview'),
        'hired': applications.filter(stage='hired'),
    }
    
    # access_requests to show if dispatcher has credential access
    access_requests = CredentialAccessRequest.objects.filter(dispatcher=profile)
    from collections import defaultdict
    request_map = defaultdict(dict)
    for req in access_requests:
        request_map[req.driver_id][req.credential_type] = req

    for app in applications:
        app.driver.access_requests_map = request_map.get(app.driver.id, {})
    for driver in pool_drivers:
        driver.access_requests_map = request_map.get(driver.id, {})
        
    tab = request.GET.get('tab', 'candidates')
    
    context = {
        'profile': profile,
        'job': job,
        'pipeline': pipeline,
        'tab': tab,
    }
    return render(request, 'companies/job_dashboard.html', context)


@login_required
def edit_job(request, job_id):
    if request.user.role != 'company':
        return redirect('/')
    messages.info(request, "Edit feature coming soon. Please close and repost if changes are needed.")
    return redirect('companies:dashboard')


@login_required
def close_job(request, job_id):
    if request.method == 'POST' and request.user.role == 'company':
        profile = request.user.company_profile
        job = get_object_or_404(JobListing, pk=job_id, company=profile)
        job.status = 'filled'
        job.save()
        messages.success(request, f'Job "{job.title}" has been closed.')
    return redirect('companies:dashboard')


@login_required
def company_profile_public(request, company_id):
    company = get_object_or_404(CompanyProfile, pk=company_id)
    jobs = company.job_listings.filter(status='active').order_by('-created_at')
    reviews = company.reviews_received.select_related('driver').order_by('-created_at')
    
    context = {
        'company': company,
        'jobs': jobs,
        'reviews': reviews,
    }
    return render(request, 'companies/public_profile.html', context)


@login_required
def view_driver_documents(request, driver_id):
    if request.user.role != 'company':
        return redirect('/')

    profile = request.user.company_profile
    target_driver = get_object_or_404(DriverProfile, pk=driver_id)

    # Verify access
    access = CredentialAccessRequest.objects.filter(
        dispatcher=profile,
        driver=target_driver,
        status='approved'
    ).exists()

    if not access:
        messages.error(request, "You do not have permission to view these documents.")
        return redirect('companies:dashboard')

    approved_credentials = list(CredentialAccessRequest.objects.filter(
        dispatcher=profile,
        driver=target_driver,
        status='approved'
    ).values_list('credential_type', flat=True))

    return render(request, 'companies/driver_documents.html', {
        'target_driver': target_driver,
        'profile': profile,
        'approved_credentials': approved_credentials,
        'credentials': target_driver.credentials.all(),
        'documents': target_driver.documents.all()
    })

@login_required
def leave_driver_review(request, driver_id):
    if request.user.role != 'company':
        return redirect('/')

    from drivers.models import DriverProfile, DriverReview
    from jobs.models import JobApplication

    target_driver = get_object_or_404(DriverProfile, pk=driver_id)
    company = request.user.company_profile

    # SECURITY CHECK: Must be hired
    if not JobApplication.objects.filter(driver=target_driver, job__company=company, stage='hired').exists():
        messages.error(request, "You can only review drivers you have hired.")
        return redirect(request.META.get('HTTP_REFERER', 'companies:dashboard'))

    # One review per driver per company
    if DriverReview.objects.filter(driver=target_driver, company=company).exists():
        messages.error(request, "You have already reviewed this driver.")
        return redirect(request.META.get('HTTP_REFERER', 'companies:dashboard'))

    if request.method == 'POST':
        DriverReview.objects.create(
            driver=target_driver,
            company=company,
            reliability=int(request.POST.get('reliability', 5)),
            punctuality=int(request.POST.get('punctuality', 5)),
            equipment=int(request.POST.get('equipment', 5)),
            communication=int(request.POST.get('communication', 5)),
            comment=request.POST.get('comment', '').strip(),
            employed_from=request.POST.get('employed_from') or None,
            employed_to=request.POST.get('employed_to') or None
        )
        messages.success(request, f"Review submitted for {target_driver.user.get_full_name()}!")
        return redirect('companies:dashboard')

    return render(request, 'companies/leave_driver_review.html', {
        'target_driver': target_driver,
        'profile': company
    })



@login_required
def job_kanban(request, job_id):
    if request.user.role != 'company':
        return redirect('/')
    profile = request.user.company_profile
    job = get_object_or_404(JobListing, id=job_id, company=profile)
    applications = job.applications.all().select_related('driver', 'driver__user').order_by('-created_at')
    
    pipeline = {
        'applied': applications.filter(stage__in=['applied', 'invited']),
        'reviewed': applications.filter(stage='reviewed'),
        'interview': applications.filter(stage='interview'),
        'hired': applications.filter(stage='hired'),
    }
    
    stats = {
        'total_applicants': applications.count(),
        'interviews_this_week': applications.filter(
            stage='interview',
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'open_positions': 1 if job.status == 'active' else 0,
    }
    
    return render(request, 'companies/job_kanban.html', {
        'profile': profile,
        'job': job,
        'pipeline': pipeline,
        'stats': stats,
    })
