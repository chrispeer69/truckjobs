from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import JobListing


def job_list(request):
    jobs = JobListing.objects.filter(status='active').select_related('company', 'city_pool')

    # Search
    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    state = request.GET.get('state', '').strip()
    
    if q:
        jobs = jobs.filter(
            models.Q(title__icontains=q) | 
            models.Q(description__icontains=q) | 
            models.Q(company__company_name__icontains=q)
        )
    if city:
        jobs = jobs.filter(
            models.Q(city_pool__name__icontains=city) | 
            models.Q(company__city__icontains=city)
        )
    if state:
        jobs = jobs.filter(
            models.Q(city_pool__state__iexact=state) | 
            models.Q(company__state__iexact=state)
        )

    # Filters
    category = request.GET.get('category', '')
    cdl = request.GET.get('cdl', '')
    employment = request.GET.get('employment', '')
    urgent = request.GET.get('urgent', '')
    bonus = request.GET.get('bonus', '')

    if category:
        jobs = jobs.filter(category=category)
    if cdl:
        jobs = jobs.filter(cdl_requirement=cdl)
    if employment:
        jobs = jobs.filter(employment_type=employment)
    if urgent:
        jobs = jobs.filter(is_urgent=True)
    if bonus:
        jobs = jobs.filter(benefits__icontains='Sign-on bonus')

    # Check if logged-in driver has applied
    applied_job_ids = []
    if request.user.is_authenticated and request.user.role == 'driver':
        try:
            applied_job_ids = list(
                request.user.driver_profile.applications.values_list('job_id', flat=True)
            )
        except Exception:
            pass

    context = {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
        'q': q,
        'city': city,
        'category': category,
        'cdl': cdl,
        'employment': employment,
        'urgent': urgent,
        'bonus': bonus,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    has_applied = False
    if request.user.is_authenticated and request.user.role == 'driver':
        try:
            has_applied = job.applications.filter(driver=request.user.driver_profile).exists()
        except Exception:
            pass
    return render(request, 'jobs/job_detail.html', {'job': job, 'has_applied': has_applied})
