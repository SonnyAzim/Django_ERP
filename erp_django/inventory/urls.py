from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'items', views.ItemViewSet, basename='items')
router.register(r'transactions', views.TransactionViewSet, basename='transactions')
router.register(r'adjustments', views.StockAdjustmentViewSet, basename='adjustments')

urlpatterns = [
    path('items/bulk_upload/', views.bulk_upload_items, name='bulk-upload'),
    path('', include(router.urls)),
]
