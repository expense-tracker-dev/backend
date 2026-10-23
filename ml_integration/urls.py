from django.urls import path
from . import views

urlpatterns = [
    path('ml/status/', views.MLStatusView.as_view(), name='ml-status'),
    path('ml/predict/daily/', views.DailyPredictionView.as_view(), name='ml-daily-predict'),
    path('ml/predict/monthly/', views.MonthlyPredictionView.as_view(), name='ml-monthly-predict'),
    path('ml/predict/future-budget/', views.FutureBudgetPredictorView.as_view(), name='ml-future-budget'),
]
