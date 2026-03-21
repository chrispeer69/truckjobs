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
    tab = request.GET.get('tab', 'pipeline')

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

    # Handle access request POST
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'request_credentials':
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
            ApplicationMessage.objects.create(
                application=application,
                sender_is_company=True,
                content=content
            )
            # Move to interview stage if they asked a question
            if application.stage in ['applied', 'reviewed', 'invited']:
                application.stage = 'interview'
            application.save()
            messages.success(request, f'Question sent to {application.driver.user.get_full_name()}.')
    
    elif action == 'request_credentials':
        # Create a pending access request if it doesn't exist
        req, created = CredentialAccessRequest.objects.get_or_create(
            dispatcher=request.user.company_profile,
            driver=application.driver,
            defaults={'status': 'pending'}
        )
        if created:
            send_access_request_mail(request.user.company_profile, application.driver)
        
        if application.stage in ['applied', 'reviewed']:
                application.stage = 'interview'
        application.save()
        messages.success(request, f'Credential access requested from {application.driver.user.get_full_name()}.')
        
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
    request_map = {req.driver_id: req for req in access_requests}

    for app in applications:
        app.driver.access_request = request_map.get(app.driver.id)
    for driver in pool_drivers:
        driver.access_request = request_map.get(driver.id)
        
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
    
    context = {
        'company': company,
        'jobs': jobs,
    }
    return render(request, 'companies/public_profile.html', context)


@login_required
def view_driver_documents(request, driver_id):
    if request.user.role != 'company':
        return redirect('/')

    profile = request.user.company_profile
    target_driver = get_object_or_404(DriverProfile, pk=driver_id)

    # Check if access is granted
    access_req = CredentialAccessRequest.objects.filter(
        dispatcher=profile,
        driver=target_driver,
        status='approved'
    ).first()

    if not access_req:
        messages.error(request, 'You do not have access to view this driver\'s documents.')
        return redirect('companies:dashboard')

    credentials = target_driver.credentials.exclude(file__exact='')
    
    return render(request, 'companies/driver_documents.html', {
        'target_driver': target_driver,
        'credentials': credentials,
    })

