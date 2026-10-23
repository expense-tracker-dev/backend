from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import date, timedelta
from .models import Transaction
from .serializers import TransactionSerializer
from categories.models import Category


class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        # Filters
        tx_type = self.request.query_params.get('type')
        category_id = self.request.query_params.get('category')
        account_id = self.request.query_params.get('account')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        month = self.request.query_params.get('month')  # format: YYYY-MM
        year = self.request.query_params.get('year')

        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if month:
            year_part, month_part = month.split('-')
            queryset = queryset.filter(date__year=year_part, date__month=month_part)
        if year:
            queryset = queryset.filter(date__year=year)
        return queryset


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionSummaryView(APIView):
    """Overall income/expense summary with optional date filters."""

    def get(self, request):
        queryset = Transaction.objects.filter(user=request.user)
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month:
            y, m = month.split('-')
            queryset = queryset.filter(date__year=y, date__month=m)
        elif year:
            queryset = queryset.filter(date__year=year)

        total_income = queryset.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or 0
        total_expense = queryset.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or 0
        net = total_income - total_expense

        return Response({
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_balance': float(net),
            'transaction_count': queryset.count(),
            'currency': request.user.currency,
        })


class IncomeFlowView(APIView):
    """Income flow analysis - sources and trends."""

    def get(self, request):
        queryset = Transaction.objects.filter(user=request.user, transaction_type='income')
        month = request.query_params.get('month')
        year = request.query_params.get('year', date.today().year)
        if month:
            y, m = month.split('-')
            queryset = queryset.filter(date__year=y, date__month=m)
        else:
            queryset = queryset.filter(date__year=year)

        # Category-wise income breakdown
        by_category = (
            queryset.values('category__name', 'category__color', 'category__icon')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        # Monthly trend (for year view)
        monthly_trend = (
            queryset.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )

        total = queryset.aggregate(s=Sum('amount'))['s'] or 0

        return Response({
            'total_income': float(total),
            'by_category': list(by_category),
            'monthly_trend': [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'total': float(item['total']),
                    'count': item['count'],
                }
                for item in monthly_trend
            ],
            'currency': request.user.currency,
        })


class ExpenseFlowView(APIView):
    """Expense flow analysis - spending patterns and trends."""

    def get(self, request):
        queryset = Transaction.objects.filter(user=request.user, transaction_type='expense')
        month = request.query_params.get('month')
        year = request.query_params.get('year', date.today().year)
        if month:
            y, m = month.split('-')
            queryset = queryset.filter(date__year=y, date__month=m)
        else:
            queryset = queryset.filter(date__year=year)

        # Category-wise expense breakdown
        by_category = (
            queryset.values('category__name', 'category__color', 'category__icon')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        # Monthly trend
        monthly_trend = (
            queryset.annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )

        # Daily trend (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        daily_trend = (
            queryset.filter(date__gte=thirty_days_ago)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )

        total = queryset.aggregate(s=Sum('amount'))['s'] or 0

        return Response({
            'total_expense': float(total),
            'by_category': list(by_category),
            'monthly_trend': [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'total': float(item['total']),
                    'count': item['count'],
                }
                for item in monthly_trend
            ],
            'daily_trend_last_30_days': [
                {
                    'date': item['day'].strftime('%Y-%m-%d'),
                    'total': float(item['total']),
                }
                for item in daily_trend
            ],
            'currency': request.user.currency,
        })


class ChartDataView(APIView):
    """Pie chart data for income and expense overview."""

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year', date.today().year)
        queryset = Transaction.objects.filter(user=request.user)
        if month:
            y, m = month.split('-')
            queryset = queryset.filter(date__year=y, date__month=m)
        else:
            queryset = queryset.filter(date__year=year)

        # Income pie chart data
        income_data = (
            queryset.filter(transaction_type='income')
            .values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        # Expense pie chart data
        expense_data = (
            queryset.filter(transaction_type='expense')
            .values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        total_income = queryset.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or 0
        total_expense = queryset.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or 0

        return Response({
            'income_chart': [
                {
                    'label': item['category__name'] or 'Uncategorized',
                    'value': float(item['total']),
                    'color': item['category__color'] or '#607D8B',
                    'percentage': round(float(item['total']) / float(total_income) * 100, 2) if total_income else 0,
                }
                for item in income_data
            ],
            'expense_chart': [
                {
                    'label': item['category__name'] or 'Uncategorized',
                    'value': float(item['total']),
                    'color': item['category__color'] or '#607D8B',
                    'percentage': round(float(item['total']) / float(total_expense) * 100, 2) if total_expense else 0,
                }
                for item in expense_data
            ],
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'currency': request.user.currency,
        })


class AccountAnalysisView(APIView):
    """Detailed analysis for a specific account."""

    def get(self, request, account_id):
        from accounts.models import Account
        try:
            account = Account.objects.get(pk=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response({'error': 'Account not found.'}, status=status.HTTP_404_NOT_FOUND)

        transactions = Transaction.objects.filter(user=request.user, account=account)
        month = request.query_params.get('month')
        if month:
            y, m = month.split('-')
            transactions = transactions.filter(date__year=y, date__month=m)

        total_income = transactions.filter(transaction_type='income').aggregate(s=Sum('amount'))['s'] or 0
        total_expense = transactions.filter(transaction_type='expense').aggregate(s=Sum('amount'))['s'] or 0

        recent = transactions.order_by('-date', '-created_at')[:10]

        return Response({
            'account': {
                'id': account.id,
                'name': account.name,
                'type': account.account_type,
                'balance': float(account.balance),
                'currency': account.currency,
            },
            'summary': {
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'net': float(total_income - total_expense),
                'transaction_count': transactions.count(),
            },
            'recent_transactions': TransactionSerializer(recent, many=True).data,
            'currency': request.user.currency,
        })
