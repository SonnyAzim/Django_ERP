"""
URL configuration for erp_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/inventory/', include('inventory.urls')),
    path('api/bom/', include('bom.urls')),
    path('api/forecasts/', include('forecasts.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/suppliers/', include('suppliers.urls')),
    path('api/valuation/', include('valuation.urls')),
    path('api/duty/', include('duty.urls')),
    path('api/production/', include('production.urls')),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/inventory/', views.inventory_page, name='inventory'),
    path('dashboard/bom/', views.bom_page, name='bom'),
    path('dashboard/forecast/', views.forecast_page, name='forecast'),
    path('dashboard/sales/', views.sales_page, name='sales'),
    path('dashboard/valuation/', views.valuation_page, name='valuation'),
    path('dashboard/duty/', views.duty_page, name='duty'),
    path('dashboard/suppliers/', views.suppliers_page, name='suppliers'),
    path('health/', views.health_check, name='health'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
