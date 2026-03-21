from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import User
from pools.models import CityPool
from drivers.models import DriverProfile
from companies.models import CompanyProfile


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Allow login by email or username
        user_obj = User.objects.filter(email=username).first() or User.objects.filter(username=username).first()
        
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = None
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            if user.role == 'driver':
                return redirect('drivers:profile')
            elif user.role == 'company':
                return redirect('companies:dashboard')
            return redirect('/')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('/')


def register_driver(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        cdl_class = request.POST.get('cdl_class', 'no_cdl')
        years_experience = request.POST.get('years_experience', 0)
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'registration/register_driver.html')

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='driver',
        )

        city_pool = CityPool.objects.filter(name__iexact=city, state__iexact=state, is_active=True).first()

        DriverProfile.objects.create(
            user=user,
            cdl_class=cdl_class,
            years_experience=int(years_experience) if years_experience else 0,
            city=city,
            state=state.upper(),
            city_pool=city_pool,
        )

        login(request, user)
        messages.success(request, 'Welcome! Complete your profile to get started.')
        return redirect('drivers:profile')

    city_pools = CityPool.objects.filter(is_active=True)
    return render(request, 'registration/register_driver.html', {'city_pools': city_pools})


def register_company(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        contact_name = request.POST.get('contact_name', '').strip()
        company_name = request.POST.get('company_name', '').strip()
        company_type = request.POST.get('company_type', 'both')
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'registration/register_company.html')

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        name_parts = contact_name.split()
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name_parts[0] if name_parts else '',
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            role='company',
        )

        city_pool = CityPool.objects.filter(name__iexact=city, state__iexact=state, is_active=True).first()

        CompanyProfile.objects.create(
            user=user,
            company_name=company_name,
            company_type=company_type,
            city=city,
            state=state.upper(),
            phone=phone,
            contact_name=contact_name,
            city_pool=city_pool,
        )

        login(request, user)
        messages.success(request, f'Welcome to DrivingJobs.online! Post your first job to start hiring.')
        return redirect('companies:post_job')

    city_pools = CityPool.objects.filter(is_active=True)
    return render(request, 'registration/register_company.html', {'city_pools': city_pools})


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=email).first()
        
        if not user:
            # User wants a red colored sentence if not found
            messages.error(request, 'No account available with this email.')
            return render(request, 'core/forgot_password.html')
        
        # Give old OTPs an expired status or just create new
        import random
        from .models import PasswordResetOTP
        from .emails import send_password_reset_otp
        
        otp_code = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.create(user=user, otp=otp_code)
        
        # Send email
        send_password_reset_otp(user, otp_code)
        
        request.session['reset_email'] = user.email
        return redirect('core:verify_otp')
        
    return render(request, 'core/forgot_password.html')


def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    email = request.session.get('reset_email')
    if not email:
        return redirect('core:forgot_password')
        
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        user = User.objects.filter(email__iexact=email).first()
        
        if user:
            from .models import PasswordResetOTP
            # Get latest OTP
            otp_record = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()
            if otp_record and otp_record.otp == otp_code and otp_record.is_valid():
                request.session['otp_verified'] = True
                return redirect('core:set_new_password')
            else:
                messages.error(request, 'Invalid or expired code. Please try again.')
        else:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('core:forgot_password')
            
    return render(request, 'core/verify_otp.html', {'email': email})


def set_new_password(request):
    if request.user.is_authenticated:
        return redirect('/')
        
    email = request.session.get('reset_email')
    verified = request.session.get('otp_verified')
    
    if not email or not verified:
        return redirect('core:forgot_password')
        
    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/set_new_password.html')
            
        user = User.objects.filter(email__iexact=email).first()
        if user:
            user.set_password(password)
            user.save()
            
            # Clean up
            from .models import PasswordResetOTP
            PasswordResetOTP.objects.filter(user=user).delete()
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
                
            messages.success(request, 'Password updated successfully! You can now log in.')
            return redirect('login')
            
    return render(request, 'core/set_new_password.html')
