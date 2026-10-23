from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """MoneyMate API root — lists all available endpoint groups."""
    return Response({
        'app': 'MoneyMate Expense Tracker API',
        'version': '1.0.0',
        'team': 'College Technical Society Project',
        'endpoints': {
            'auth': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'refresh': '/api/auth/refresh/',
                'profile': '/api/auth/profile/',
            },
            'accounts_screen': {
                'list_create': '/api/accounts/',
                'detail': '/api/accounts/<id>/',
                'summary': '/api/accounts/summary/',
                'update_balance': '/api/accounts/<id>/balance/',
            },
            'categories_screen': {
                'list_create': '/api/categories/',
                'detail': '/api/categories/<id>/',
                'initialize_defaults': '/api/categories/initialize/',
            },
            'record_screen': {
                'list_create': '/api/transactions/',
                'detail': '/api/transactions/<id>/',
                'summary': '/api/transactions/summary/',
            },
            'budgets_screen': {
                'list_create': '/api/budgets/',
                'detail': '/api/budgets/<id>/',
                'overview': '/api/budgets/overview/',
            },
            'charts_screen': {
                'chart_data': '/api/analytics/charts/',
                'income_flow': '/api/analytics/income-flow/',
                'expense_flow': '/api/analytics/expense-flow/',
                'account_analysis': '/api/analytics/account/<id>/',
            },
            'split_screen': {
                'list_create': '/api/splits/',
                'detail': '/api/splits/<id>/',
                'mark_paid': '/api/splits/<id>/mark-paid/',
                'equal_calculator': '/api/splits/calculator/equal/',
            },
            'cash_calculator': '/api/calculator/cash/',
            'future_budget_predictor_ml': {
                'status': '/api/ml/status/',
                'daily_prediction': '/api/ml/predict/daily/',
                'monthly_prediction': '/api/ml/predict/monthly/',
                'full_predictor': '/api/ml/predict/future-budget/',
            },
            'admin': '/admin/',
        },
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('categories.urls')),
    path('api/', include('transactions.urls')),
    path('api/', include('budgets.urls')),
    path('api/', include('splits.urls')),
    path('api/', include('ml_integration.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
