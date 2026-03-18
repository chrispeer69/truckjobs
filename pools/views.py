from django.shortcuts import render
from .models import CityPool


def pool_list(request):
    pools = CityPool.objects.all().order_by('-is_active', 'state', 'name')
    user_pool = None
    if request.user.is_authenticated:
        if request.user.role == 'driver':
            try:
                user_pool = request.user.driver_profile.city_pool
            except Exception:
                pass
        elif request.user.role == 'company':
            try:
                user_pool = request.user.company_profile.city_pool
            except Exception:
                pass
    return render(request, 'pools/pool_list.html', {'pools': pools, 'user_pool': user_pool})
