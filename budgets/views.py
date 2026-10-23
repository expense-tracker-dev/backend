from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date
from .models import Budget
from .serializers import BudgetSerializer
from categories.models import Category
from transactions.models import Transaction
from django.db.models import Sum


class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        queryset = Budget.objects.filter(user=self.request.user)
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year', date.today().year)
        if month:
            queryset = queryset.filter(month=month, year=year)
        return queryset


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class BudgetOverviewView(APIView):
    """Overview of budgeted vs non-budgeted categories for a given month."""

    def get(self, request):
        today = date.today()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))

        budgets = Budget.objects.filter(user=request.user, month=month, year=year)
        budgeted_category_ids = budgets.values_list('category_id', flat=True)

        # Non-budgeted expense categories that have actual expenses
        non_budgeted = Category.objects.filter(
            user=request.user,
            category_type='expense',
        ).exclude(id__in=budgeted_category_ids)

        non_budgeted_with_expense = []
        for cat in non_budgeted:
            spent = Transaction.objects.filter(
                user=request.user,
                category=cat,
                transaction_type='expense',
                date__year=year,
                date__month=month,
            ).aggregate(s=Sum('amount'))['s'] or 0
            if spent > 0:
                non_budgeted_with_expense.append({
                    'category_id': cat.id,
                    'category_name': cat.name,
                    'category_color': cat.color,
                    'category_icon': cat.icon,
                    'spent': float(spent),
                })

        total_budget = budgets.aggregate(s=Sum('amount'))['s'] or 0
        total_spent = sum(
            float(
                Transaction.objects.filter(
                    user=request.user,
                    category_id=b.category_id,
                    transaction_type='expense',
                    date__year=year,
                    date__month=month,
                ).aggregate(s=Sum('amount'))['s'] or 0
            )
            for b in budgets
        )

        return Response({
            'month': month,
            'year': year,
            'total_budget': float(total_budget),
            'total_spent': float(total_spent),
            'total_remaining': max(float(total_budget) - float(total_spent), 0),
            'budgeted_categories': BudgetSerializer(budgets, many=True, context={'request': request}).data,
            'non_budgeted_categories_with_expense': non_budgeted_with_expense,
        })
