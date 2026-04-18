from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.BoMViewSet, basename='bom')

urlpatterns = [
    path('bulk_upload/', views.bulk_upload_bom, name='bom-bulk-upload'),
    path('', include(router.urls)),
]
