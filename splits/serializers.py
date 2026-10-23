from rest_framework import serializers
from .models import SplitExpense, SplitMember


class SplitMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitMember
        fields = ['id', 'name', 'email', 'share_amount', 'share_percentage', 'is_paid', 'paid_at', 'notes']
        read_only_fields = ['id']


class SplitExpenseSerializer(serializers.ModelSerializer):
    members = SplitMemberSerializer(many=True)
    settled_amount = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField()
    settled_count = serializers.SerializerMethodField()

    class Meta:
        model = SplitExpense
        fields = [
            'id', 'title', 'description', 'total_amount', 'date', 'category', 'account',
            'status', 'members', 'settled_amount', 'pending_amount', 'settled_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_settled_amount(self, obj):
        return float(sum(m.share_amount for m in obj.members.filter(is_paid=True)))

    def get_pending_amount(self, obj):
        return float(sum(m.share_amount for m in obj.members.filter(is_paid=False)))

    def get_settled_count(self, obj):
        return obj.members.filter(is_paid=True).count()

    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        validated_data['user'] = self.context['request'].user
        split_expense = SplitExpense.objects.create(**validated_data)
        total = float(split_expense.total_amount)
        for member_data in members_data:
            if total > 0:
                member_data['share_percentage'] = round(
                    float(member_data.get('share_amount', 0)) / total * 100, 2
                )
            SplitMember.objects.create(split_expense=split_expense, **member_data)
        return split_expense

    def update(self, instance, validated_data):
        members_data = validated_data.pop('members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members_data is not None:
            instance.members.all().delete()
            for member_data in members_data:
                SplitMember.objects.create(split_expense=instance, **member_data)
        return instance


class MarkMemberPaidSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
    is_paid = serializers.BooleanField()


class EqualSplitCalculatorSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    num_people = serializers.IntegerField(min_value=1, max_value=100)
