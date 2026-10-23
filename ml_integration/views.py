import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

ML_BASE_URL = settings.ML_BASE_URL
ML_TIMEOUT = getattr(settings, 'ML_API_TIMEOUT', 30)


def fetch_ml_endpoint(endpoint: str):
    """
    Helper to call the ML API with full error handling.
    Returns (data, error) tuple. On success error is None; on failure data is None.
    """
    url = f"{ML_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=ML_TIMEOUT)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.Timeout:
        logger.error(f"ML API timeout for endpoint: {endpoint}")
        return None, {
            'error': 'ML service is currently waking up (Render free tier cold start). Please retry in 30 seconds.',
            'code': 'TIMEOUT',
        }
    except requests.exceptions.ConnectionError:
        logger.error(f"ML API connection error for endpoint: {endpoint}")
        return None, {
            'error': 'Cannot connect to ML service. Please check your network or if the service is running.',
            'code': 'CONNECTION_ERROR',
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"ML API HTTP error for endpoint {endpoint}: {e}")
        return None, {
            'error': f'ML service returned an error: {str(e)}',
            'code': 'HTTP_ERROR',
        }
    except Exception as e:
        logger.error(f"Unexpected ML API error for {endpoint}: {e}")
        return None, {
            'error': 'An unexpected error occurred while fetching ML predictions.',
            'code': 'UNKNOWN_ERROR',
        }


class MLStatusView(APIView):
    """Check ML API health/availability."""

    def get(self, request):
        data, error = fetch_ml_endpoint('/')
        if error:
            return Response({
                'ml_service': 'unavailable',
                'error': error,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({
            'ml_service': 'available',
            'response': data,
        })


class DailyPredictionView(APIView):
    """
    Get daily expense prediction from the ML service.
    Enriches with the user's actual spending today for comparison.

    ML Response shape:
    {
        "date": "2026-10-20",
        "predicted_expense": 230.22,
        "currency": "INR"
    }
    """

    def get(self, request):
        data, error = fetch_ml_endpoint('/predict/daily')
        if error:
            return Response({
                'success': False,
                'error': error,
                'fallback_message': 'ML service is unavailable. Please try again in 30 seconds.',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        from transactions.models import Transaction
        from django.db.models import Sum
        from datetime import date

        today = date.today()
        actual_today = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date=today,
        ).aggregate(s=Sum('amount'))['s'] or 0

        return Response({
            'success': True,
            'prediction': data,
            'user_context': {
                'actual_spending_today': float(actual_today),
                'currency': request.user.currency,
                'note': 'ML prediction is based on historical dataset, not your personal transaction history.',
            },
        })


class MonthlyPredictionView(APIView):
    """
    Get monthly expense prediction from the ML service.
    Includes user's actual month-to-date data and potential savings estimate.

    ML Response shape:
    {
        "current_month": "October 2026",
        "estimated_month_end_expense": 6340.54,
        "next_month": "November 2026",
        "predicted_next_month_expense": 6035.37,
        "currency": "INR"
    }
    """

    def get(self, request):
        data, error = fetch_ml_endpoint('/predict/monthly')
        if error:
            return Response({
                'success': False,
                'error': error,
                'fallback_message': 'ML service is unavailable. Please try again in 30 seconds.',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        from transactions.models import Transaction
        from django.db.models import Sum
        from datetime import date

        today = date.today()
        actual_expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__year=today.year,
            date__month=today.month,
        ).aggregate(s=Sum('amount'))['s'] or 0

        actual_income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date__year=today.year,
            date__month=today.month,
        ).aggregate(s=Sum('amount'))['s'] or 0

        predicted_next = data.get('predicted_next_month_expense', 0)
        potential_savings = max(float(actual_income) - float(predicted_next), 0)

        return Response({
            'success': True,
            'prediction': data,
            'user_context': {
                'actual_expense_this_month': float(actual_expense),
                'actual_income_this_month': float(actual_income),
                'potential_savings_next_month': potential_savings,
                'currency': request.user.currency,
                'note': 'ML uses historical dataset. Predictions are estimates only.',
            },
        })


class FutureBudgetPredictorView(APIView):
    """
    Main endpoint for the Future Budget Predictor screen.
    Aggregates daily + monthly ML predictions with user's own financial summary.
    """

    def get(self, request):
        daily_data, daily_error = fetch_ml_endpoint('/predict/daily')
        monthly_data, monthly_error = fetch_ml_endpoint('/predict/monthly')

        from transactions.models import Transaction
        from django.db.models import Sum, Count
        from datetime import date, timedelta

        today = date.today()

        # This month's totals
        this_month_expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__year=today.year,
            date__month=today.month,
        ).aggregate(s=Sum('amount'))['s'] or 0

        this_month_income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date__year=today.year,
            date__month=today.month,
        ).aggregate(s=Sum('amount'))['s'] or 0

        # Top 5 expense categories this month
        top_categories = (
            Transaction.objects.filter(
                user=request.user,
                transaction_type='expense',
                date__year=today.year,
                date__month=today.month,
            )
            .values('category__name', 'category__color', 'category__icon')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:5]
        )

        # Last 3 months average daily expense
        ninety_days_ago = today - timedelta(days=90)
        avg_daily = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__gte=ninety_days_ago,
        ).aggregate(s=Sum('amount'))['s'] or 0
        avg_daily_expense = round(float(avg_daily) / 90, 2)

        return Response({
            'success': True,
            'daily_prediction': daily_data,
            'monthly_prediction': monthly_data,
            'ml_errors': {
                'daily': daily_error,
                'monthly': monthly_error,
            } if (daily_error or monthly_error) else None,
            'user_financial_summary': {
                'expense_this_month': float(this_month_expense),
                'income_this_month': float(this_month_income),
                'savings_this_month': max(float(this_month_income) - float(this_month_expense), 0),
                'avg_daily_expense_last_90_days': avg_daily_expense,
                'top_expense_categories': [
                    {
                        'category': item['category__name'] or 'Uncategorized',
                        'color': item['category__color'],
                        'icon': item['category__icon'],
                        'amount': float(item['total']),
                        'transaction_count': item['count'],
                    }
                    for item in top_categories
                ],
                'currency': request.user.currency,
            },
            'disclaimer': (
                'ML predictions use a shared historical dataset and are not based on your '
                'personal transaction history. Values are estimates only.'
            ),
        })
