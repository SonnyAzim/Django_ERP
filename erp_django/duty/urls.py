from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'hs-codes', views.HSCodeViewSet, basename='hs-codes')
router.register(r'item-links', views.ItemHSCodeViewSet, basename='item-hs-codes')
router.register(r'calculator', views.DutyCalculatorViewSet, basename='duty-calculator')

urlpatterns = [
    path('', include(router.urls)),
]
