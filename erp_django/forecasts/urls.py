from django.urls import path
from . import views

urlpatterns = [
    path('forecasts/', views.ForecastListView.as_view(), name='forecast-list'),
    path('forecasts/upload/', views.ForecastUploadView.as_view(), name='forecast-upload'),
    path('forecasts/rolling-months/', views.RollingMonthsView.as_view(), name='rolling-months'),
    path('mrp/', views.MRPCalculateView.as_view(), name='mrp-calculate'),
    path('mrp/material-requirements/', views.MaterialRequirementsView.as_view(), name='mrp-materials'),
    path('mrp/order-plan/', views.OrderPlanView.as_view(), name='mrp-order-plan'),
    path('pipeline/', views.PipelineView.as_view(), name='pipeline-list'),
    path('pipeline/<int:pk>/', views.PipelineView.as_view(), name='pipeline-detail'),
]
