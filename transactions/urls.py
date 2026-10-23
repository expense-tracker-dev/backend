from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.TransactionListCreateView.as_view(), name='transaction-list'),
    path('transactions/summary/', views.TransactionSummaryView.as_view(), name='transaction-summary'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('analytics/income-flow/', views.IncomeFlowView.as_view(), name='income-flow'),
    path('analytics/expense-flow/', views.ExpenseFlowView.as_view(), name='expense-flow'),
    path('analytics/charts/', views.ChartDataView.as_view(), name='chart-data'),
    path('analytics/account/<int:account_id>/', views.AccountAnalysisView.as_view(), name='account-analysis'),
]
