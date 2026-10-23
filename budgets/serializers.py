from rest_framework import serializers
from .models import Budget
from categories.serializers import CategorySerializer


class BudgetSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'category_detail', 'amount', 'month', 'year',
            'alert_threshold', 'spent', 'remaining', 'progress_percentage',
            'is_over_budget', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _get_spent(self, obj):
        from transactions.models import Transaction
        from django.db.models import Sum
        spent = Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            transaction_type='expense',
            date__year=obj.year,
            date__month=obj.month,
        ).aggregate(s=Sum('amount'))['s'] or 0
        return float(spent)

    def get_spent(self, obj):
        return self._get_spent(obj)

    def get_remaining(self, obj):
        spent = self._get_spent(obj)
        return max(float(obj.amount) - spent, 0)

    def get_progress_percentage(self, obj):
        spent = self._get_spent(obj)
        if float(obj.amount) == 0:
            return 0
        return min(round(spent / float(obj.amount) * 100, 2), 100)

    def get_is_over_budget(self, obj):
        return self._get_spent(obj) > float(obj.amount)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
