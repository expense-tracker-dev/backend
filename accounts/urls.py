from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    # Financial Accounts
    path('accounts/', views.AccountListCreateView.as_view(), name='account-list'),
    path('accounts/summary/', views.AccountSummaryView.as_view(), name='account-summary'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/balance/', views.AccountBalanceUpdateView.as_view(), name='account-balance'),
]
