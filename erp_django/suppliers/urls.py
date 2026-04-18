from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.SupplierViewSet, basename='suppliers')
router.register(r'links', views.ItemSupplierViewSet, basename='item-suppliers')

urlpatterns = [
    path('', include(router.urls)),
]
