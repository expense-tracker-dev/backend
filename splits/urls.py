from django.urls import path
from . import views

urlpatterns = [
    path('splits/', views.SplitExpenseListCreateView.as_view(), name='split-list'),
    path('splits/calculator/equal/', views.EqualSplitCalculatorView.as_view(), name='split-calculator'),
    path('splits/<int:pk>/', views.SplitExpenseDetailView.as_view(), name='split-detail'),
    path('splits/<int:split_id>/mark-paid/', views.MarkMemberPaidView.as_view(), name='split-mark-paid'),
    path('calculator/cash/', views.CashCalculatorView.as_view(), name='cash-calculator'),
]
