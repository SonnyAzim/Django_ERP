from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.ValuationSummaryView.as_view()),
    path('by-category/', views.ValuationByCategoryView.as_view()),
    path('by-item-group/', views.ValuationByItemGroupView.as_view()),
    path('top-assets/', views.TopAssetsView.as_view()),
    path('exposure-analysis/', views.ExposureAnalysisView.as_view()),
    path('kpi/', views.ValuationKPIView.as_view()),
]
