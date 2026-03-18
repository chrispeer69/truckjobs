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

    # Pipeline data
    company_jobs = profile.job_listings.all()
    applications = JobApplication.objects.filter(job__company=profile).select_related('driver', 'driver__user', 'job')

    pipeline = {
        'applied': applications.filter(stage='applied'),
        'reviewed': applications.filter(stage='reviewed'),
        'interview': applications.filter(stage='interview'),
        'hired': applications.filter(stage='hired'),
    }

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
        'pipeline': pipeline,
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
    if request.user.role != 'company':
        return redirect('/')

    application = get_object_or_404(JobApplication, pk=app_id, job__company=request.user.company_profile)

    if request.method == 'POST':
        new_stage = request.POST.get('stage', '')
        valid_stages = ['applied', 'reviewed', 'interview', 'hired']
        if new_stage in valid_stages:
            application.stage = new_stage
            application.save()
            messages.success(request, f'Moved {application.driver.user.get_full_name()} to {application.get_stage_display()}.')

    return redirect('companies:dashboard')
