from rest_framework import serializers
from .models import Transaction
from categories.serializers import CategorySerializer
from accounts.serializers import AccountSerializer


class TransactionSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    account_detail = AccountSerializer(source='account', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_detail', 'category', 'category_detail',
            'transaction_type', 'amount', 'title', 'description', 'date', 'time',
            'to_account', 'is_recurring', 'tags', 'attachment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'time', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        account = data.get('account')
        if account and account.user != user:
            raise serializers.ValidationError('Account does not belong to this user.')
        category = data.get('category')
        if category and category.user != user:
            raise serializers.ValidationError('Category does not belong to this user.')
        if data.get('transaction_type') == 'transfer' and not data.get('to_account'):
            raise serializers.ValidationError('Transfer transactions require a destination account.')
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSummarySerializer(serializers.Serializer):
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
