from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.SalesOrderViewSet, basename='sales-orders')
router.register(r'deliveries', views.DeliveryViewSet, basename='deliveries')

urlpatterns = [
    path('', include(router.urls)),
]
