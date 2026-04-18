"""
Core views for the ERP system.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {'page': 'dashboard'})


@login_required
def inventory_page(request):
    return render(request, 'core/inventory.html', {'page': 'inventory'})


@login_required
def bom_page(request):
    return render(request, 'core/bom.html', {'page': 'bom'})


@login_required
def forecast_page(request):
    return render(request, 'core/forecast.html', {'page': 'forecast'})


@login_required
def sales_page(request):
    return render(request, 'core/sales.html', {'page': 'sales'})


@login_required
def valuation_page(request):
    return render(request, 'core/valuation.html', {'page': 'valuation'})


@login_required
def duty_page(request):
    return render(request, 'core/duty.html', {'page': 'duty'})


@login_required
def suppliers_page(request):
    return render(request, 'core/suppliers.html', {'page': 'suppliers'})


@require_http_methods(["GET"])
def health_check(request):
    return JsonResponse({'status': 'ok'})
