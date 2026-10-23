from django.urls import path
from . import views

urlpatterns = [
    path('budgets/', views.BudgetListCreateView.as_view(), name='budget-list'),
    path('budgets/overview/', views.BudgetOverviewView.as_view(), name='budget-overview'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget-detail'),
]
