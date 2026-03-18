import json
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pools.models import CityPool
from drivers.models import DriverProfile, Credential, DriverReview
from companies.models import CompanyProfile
from jobs.models import JobListing, JobApplication

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample data for demo/development'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # ── Cities ──
        columbus, _ = CityPool.objects.get_or_create(name='Columbus', state='OH', defaults={'is_active': True})
        cleveland, _ = CityPool.objects.get_or_create(name='Cleveland', state='OH', defaults={'is_active': True})
        cincinnati, _ = CityPool.objects.get_or_create(name='Cincinnati', state='OH', defaults={'is_active': True})
        CityPool.objects.get_or_create(name='Detroit', state='MI', defaults={'is_active': False})
        CityPool.objects.get_or_create(name='Indianapolis', state='IN', defaults={'is_active': False})
        self.stdout.write(self.style.SUCCESS('  ✓ Cities created'))

        # ── Company Users ──
        company_data = [
            {'username': 'ace_towing', 'email': 'dispatch@acetowing.com', 'first_name': 'Mike', 'last_name': 'Reynolds',
             'company_name': 'Ace Towing', 'company_type': 'towing', 'city': 'Columbus', 'state': 'OH',
             'phone': '(614) 555-0101', 'years_in_operation': 12, 'city_pool': columbus},
            {'username': 'maxfreight', 'email': 'hr@maxfreight.com', 'first_name': 'Sarah', 'last_name': 'Chen',
             'company_name': 'MaxFreight Logistics', 'company_type': 'freight', 'city': 'Columbus', 'state': 'OH',
             'phone': '(614) 555-0202', 'years_in_operation': 8, 'city_pool': columbus},
            {'username': 'buckeye_recovery', 'email': 'ops@buckeyerecovery.com', 'first_name': 'Jim', 'last_name': 'Watson',
             'company_name': 'Buckeye Recovery Services', 'company_type': 'towing', 'city': 'Columbus', 'state': 'OH',
             'phone': '(614) 555-0303', 'years_in_operation': 20, 'city_pool': columbus},
        ]

        companies = []
        for cd in company_data:
            user, created = User.objects.get_or_create(username=cd['username'], defaults={
                'email': cd['email'], 'first_name': cd['first_name'], 'last_name': cd['last_name'], 'role': 'company',
            })
            if created:
                user.set_password('demo1234')
                user.save()
            profile, _ = CompanyProfile.objects.get_or_create(user=user, defaults={
                'company_name': cd['company_name'], 'company_type': cd['company_type'],
                'city': cd['city'], 'state': cd['state'], 'phone': cd['phone'],
                'years_in_operation': cd['years_in_operation'], 'contact_name': f"{cd['first_name']} {cd['last_name']}",
                'city_pool': cd['city_pool'],
            })
            companies.append(profile)
        self.stdout.write(self.style.SUCCESS('  ✓ Companies created'))

        # ── Driver Users ──
        driver_data = [
            {'username': 'jmiller', 'email': 'jmiller@email.com', 'first_name': 'James', 'last_name': 'Miller',
             'cdl_class': 'cdl_a', 'years_experience': 8, 'specialties': 'flatbed,rollback,heavy-duty',
             'availability': 'employed_open', 'min_pay_hourly': 28, 'preferred_shift': 'day',
             'city': 'Columbus', 'state': 'OH', 'city_pool': columbus, 'equipment_experience': 'Flatbed, wheel-lift, integrated', 'last_employer': 'Ace Towing'},
            {'username': 'twashington', 'email': 'twash@email.com', 'first_name': 'Tyrone', 'last_name': 'Washington',
             'cdl_class': 'cdl_b', 'years_experience': 4, 'specialties': 'rollback',
             'availability': 'actively_hunting', 'min_pay_hourly': 22, 'preferred_shift': 'rotating',
             'city': 'Columbus', 'state': 'OH', 'city_pool': columbus, 'equipment_experience': 'Rollback, wheel-lift', 'last_employer': ''},
            {'username': 'rjohnson', 'email': 'rjohnson@email.com', 'first_name': 'Robert', 'last_name': 'Johnson',
             'cdl_class': 'cdl_a', 'years_experience': 12, 'specialties': 'heavy-duty,hazmat',
             'availability': 'not_looking', 'min_pay_hourly': 35, 'preferred_shift': 'night',
             'city': 'Columbus', 'state': 'OH', 'city_pool': columbus, 'equipment_experience': 'Heavy-duty rotator, integrated', 'last_employer': 'Buckeye Recovery Services'},
            {'username': 'mgarcia', 'email': 'mgarcia@email.com', 'first_name': 'Maria', 'last_name': 'Garcia',
             'cdl_class': 'cdl_a', 'years_experience': 6, 'specialties': 'box truck,26ft',
             'availability': 'actively_hunting', 'min_pay_hourly': 24, 'preferred_shift': 'day',
             'city': 'Columbus', 'state': 'OH', 'city_pool': columbus, 'equipment_experience': '26ft box truck, sprinter van', 'last_employer': 'MaxFreight Logistics'},
            {'username': 'dlee', 'email': 'dlee@email.com', 'first_name': 'David', 'last_name': 'Lee',
             'cdl_class': 'cdl_b', 'years_experience': 2, 'specialties': 'flatbed',
             'availability': 'actively_hunting', 'min_pay_hourly': 20, 'preferred_shift': 'flexible',
             'city': 'Cleveland', 'state': 'OH', 'city_pool': cleveland, 'equipment_experience': 'Flatbed', 'last_employer': ''},
        ]

        drivers = []
        for dd in driver_data:
            user, created = User.objects.get_or_create(username=dd['username'], defaults={
                'email': dd['email'], 'first_name': dd['first_name'], 'last_name': dd['last_name'], 'role': 'driver',
            })
            if created:
                user.set_password('demo1234')
                user.save()
            profile, _ = DriverProfile.objects.get_or_create(user=user, defaults={
                'cdl_class': dd['cdl_class'], 'years_experience': dd['years_experience'],
                'specialties': dd['specialties'], 'availability': dd['availability'],
                'min_pay_hourly': dd['min_pay_hourly'], 'preferred_shift': dd['preferred_shift'],
                'city': dd['city'], 'state': dd['state'], 'city_pool': dd['city_pool'],
                'equipment_experience': dd['equipment_experience'], 'last_employer': dd['last_employer'],
                'is_identity_verified': True, 'is_active': True,
            })
            drivers.append(profile)
        self.stdout.write(self.style.SUCCESS('  ✓ Drivers created'))

        # ── Credentials ──
        today = date.today()
        cred_data = [
            (drivers[0], 'cdl', 'verified', today + timedelta(days=400)),
            (drivers[0], 'dot_medical', 'verified', today + timedelta(days=180)),
            (drivers[0], 'mvr', 'verified', today + timedelta(days=90)),
            (drivers[0], 'drug_test', 'verified', today + timedelta(days=60)),
            (drivers[0], 'wreckmaster', 'verified', today + timedelta(days=300)),
            (drivers[1], 'cdl', 'verified', today + timedelta(days=250)),
            (drivers[1], 'dot_medical', 'pending', today + timedelta(days=45)),
            (drivers[1], 'drug_test', 'verified', today + timedelta(days=120)),
            (drivers[2], 'cdl', 'verified', today + timedelta(days=500)),
            (drivers[2], 'dot_medical', 'verified', today + timedelta(days=200)),
            (drivers[2], 'mvr', 'verified', today + timedelta(days=150)),
            (drivers[2], 'drug_test', 'verified', today + timedelta(days=180)),
            (drivers[2], 'hazmat', 'verified', today + timedelta(days=350)),
            (drivers[3], 'cdl', 'verified', today + timedelta(days=300)),
            (drivers[3], 'dot_medical', 'expired', today - timedelta(days=10)),
        ]
        for driver, ctype, status, expiry in cred_data:
            Credential.objects.get_or_create(driver=driver, credential_type=ctype, defaults={
                'status': status, 'expiry_date': expiry,
            })
        self.stdout.write(self.style.SUCCESS('  ✓ Credentials created'))

        # ── Reviews ──
        review_data = [
            (drivers[0], companies[0], 5, 5, 4, 5, 'James is one of the most reliable operators we\'ve had. Always on time and takes great care of equipment.', today - timedelta(days=180), today - timedelta(days=30)),
            (drivers[0], companies[2], 4, 5, 5, 4, 'Solid operator. Great with heavy-duty recoveries. Would hire back anytime.', today - timedelta(days=365), today - timedelta(days=200)),
            (drivers[2], companies[0], 5, 5, 5, 5, 'Robert is the gold standard. 12 years experience shows in everything he does.', today - timedelta(days=730), today - timedelta(days=365)),
            (drivers[3], companies[1], 4, 4, 4, 3, 'Maria is a dependable box truck driver. Keep improving communication and will be excellent.', today - timedelta(days=200), today - timedelta(days=60)),
        ]
        for driver, company, rel, pun, equip, comm, comment, efrom, eto in review_data:
            DriverReview.objects.get_or_create(driver=driver, company=company, defaults={
                'reliability': rel, 'punctuality': pun, 'equipment': equip, 'communication': comm,
                'comment': comment, 'employed_from': efrom, 'employed_to': eto,
            })
        self.stdout.write(self.style.SUCCESS('  ✓ Reviews created'))

        # ── Jobs ──
        job_data = [
            {
                'company': companies[0], 'city_pool': columbus,
                'title': 'Flatbed Tow Truck Operator — Day Shift',
                'category': 'tow_truck', 'employment_type': 'full_time', 'cdl_requirement': 'cdl_a',
                'experience_years': 2, 'pay_min': 24, 'pay_max': 32, 'pay_type': 'hourly',
                'description': 'Ace Towing is looking for an experienced flatbed tow truck operator for our busy Columbus location. You\'ll handle light to medium-duty towing, roadside assistance, and private property impounds.\n\nRequirements:\n- Valid CDL-A\n- 2+ years towing experience\n- Clean MVR\n- Able to work day shift (6 AM - 6 PM)\n\nBenefits include health insurance, weekly pay, and a take-home truck.',
                'benefits': json.dumps(['Health insurance', 'Weekly pay', 'Take-home truck', 'Overtime available']),
                'is_urgent': True, 'status': 'active',
            },
            {
                'company': companies[1], 'city_pool': columbus,
                'title': '26ft Box Truck Driver — Regional Routes',
                'category': 'box_truck', 'employment_type': 'full_time', 'cdl_requirement': 'cdl_b',
                'experience_years': 1, 'pay_min': 22, 'pay_max': 27, 'pay_type': 'hourly',
                'description': 'MaxFreight Logistics seeks a reliable box truck driver for regional delivery routes in the Columbus metro area. Home daily. No overnight runs.\n\nRequirements:\n- CDL-B or higher\n- 1+ year driving experience\n- Good MVR\n- Able to lift up to 50 lbs\n\nGreat benefits and growth opportunities.',
                'benefits': json.dumps(['Health insurance', 'Dental/vision', '401k', 'Paid time off', 'Weekly pay']),
                'is_urgent': False, 'status': 'active',
            },
            {
                'company': companies[2], 'city_pool': columbus,
                'title': 'Heavy-Duty Recovery Operator — Night Shift',
                'category': 'tow_truck', 'employment_type': 'full_time', 'cdl_requirement': 'cdl_a',
                'experience_years': 5, 'pay_min': 30, 'pay_max': 42, 'pay_type': 'hourly',
                'description': 'Buckeye Recovery needs an experienced heavy-duty recovery operator for overnight shift. Must be comfortable with rotator operations and heavy commercial vehicle recovery.\n\nRequirements:\n- CDL-A with rotator experience\n- 5+ years heavy-duty recovery\n- WreckMaster certification preferred\n- Clean background and drug test\n\nTop pay for top talent. Sign-on bonus available.',
                'benefits': json.dumps(['Health insurance', 'Sign-on bonus', 'Overtime available', 'Fuel card', 'Daily pay option']),
                'is_urgent': False, 'status': 'active',
            },
            {
                'company': companies[0], 'city_pool': columbus,
                'title': 'Wheel-Lift Operator — Part Time Weekends',
                'category': 'tow_truck', 'employment_type': 'part_time', 'cdl_requirement': 'no_cdl',
                'experience_years': 0, 'pay_min': 18, 'pay_max': 22, 'pay_type': 'hourly',
                'description': 'Looking for a part-time wheel-lift operator for weekends. Great opportunity to get started in the towing industry. Will train the right person.\n\nRequirements:\n- Valid driver\'s license\n- Clean MVR\n- Able to work weekends',
                'benefits': json.dumps(['Weekly pay', 'Uniforms provided']),
                'is_urgent': False, 'status': 'active',
            },
        ]
        jobs = []
        for jd in job_data:
            job, _ = JobListing.objects.get_or_create(
                title=jd['title'], company=jd['company'],
                defaults={k: v for k, v in jd.items() if k not in ('company',)}
            )
            jobs.append(job)
        self.stdout.write(self.style.SUCCESS('  ✓ Jobs created'))

        # ── Applications ──
        app_data = [
            (jobs[0], drivers[0], 'interview'),
            (jobs[0], drivers[1], 'applied'),
            (jobs[1], drivers[3], 'reviewed'),
            (jobs[2], drivers[0], 'applied'),
            (jobs[3], drivers[1], 'hired'),
        ]
        for job, driver, stage in app_data:
            JobApplication.objects.get_or_create(job=job, driver=driver, defaults={'stage': stage})
        self.stdout.write(self.style.SUCCESS('  ✓ Applications created'))

        # ── Superuser ──
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@drivingjobs.online', 'admin1234', role='company')
            self.stdout.write(self.style.SUCCESS('  ✓ Admin superuser created (admin / admin1234)'))

        self.stdout.write(self.style.SUCCESS('\n✅ Seed data complete!'))
        self.stdout.write(f'  Login as driver: jmiller / demo1234')
        self.stdout.write(f'  Login as company: ace_towing / demo1234')
        self.stdout.write(f'  Login as admin: admin / admin1234')
