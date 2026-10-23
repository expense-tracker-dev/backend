from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import SplitExpense, SplitMember
from .serializers import (
    SplitExpenseSerializer,
    MarkMemberPaidSerializer,
    EqualSplitCalculatorSerializer,
)


class SplitExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = SplitExpenseSerializer

    def get_queryset(self):
        queryset = SplitExpense.objects.filter(user=self.request.user).prefetch_related('members')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class SplitExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SplitExpenseSerializer

    def get_queryset(self):
        return SplitExpense.objects.filter(user=self.request.user).prefetch_related('members')


class MarkMemberPaidView(APIView):
    """Mark a split member as paid or unpaid."""

    def post(self, request, split_id):
        try:
            split = SplitExpense.objects.get(pk=split_id, user=request.user)
        except SplitExpense.DoesNotExist:
            return Response({'error': 'Split expense not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MarkMemberPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data['member_id']
        is_paid = serializer.validated_data['is_paid']

        try:
            member = split.members.get(pk=member_id)
        except SplitMember.DoesNotExist:
            return Response({'error': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)

        member.is_paid = is_paid
        member.paid_at = timezone.now() if is_paid else None
        member.save()

        # Auto-update split status
        total_members = split.members.count()
        paid_members = split.members.filter(is_paid=True).count()
        if paid_members == 0:
            split.status = 'pending'
        elif paid_members == total_members:
            split.status = 'settled'
        else:
            split.status = 'partial'
        split.save()

        return Response({
            'message': f"Member marked as {'paid' if is_paid else 'unpaid'}.",
            'split': SplitExpenseSerializer(split).data,
        })


class EqualSplitCalculatorView(APIView):
    """Calculate equal split amount for N people."""

    def post(self, request):
        serializer = EqualSplitCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        total = float(serializer.validated_data['total_amount'])
        num_people = serializer.validated_data['num_people']
        per_person = round(total / num_people, 2)
        remainder = round(total - (per_person * num_people), 2)
        return Response({
            'total_amount': total,
            'num_people': num_people,
            'per_person': per_person,
            'remainder': remainder,
            'note': (
                f"First person pays {round(per_person + remainder, 2)} due to rounding."
                if remainder != 0 else "Equal split - no rounding needed."
            ),
        })


class CashCalculatorView(APIView):
    """
    Calculate total cash from currency denominations (INR).

    POST body example:
    {
        "denominations": {
            "2000": 2,
            "500": 5,
            "200": 1,
            "100": 3,
            "50": 4,
            "20": 2,
            "10": 5,
            "5": 6,
            "2": 3,
            "1": 10
        }
    }
    """

    VALID_DENOMINATIONS = [2000, 500, 200, 100, 50, 20, 10, 5, 2, 1]

    def post(self, request):
        denominations = request.data.get('denominations', {})
        total = 0
        breakdown = []
        errors = []

        for denom, count in denominations.items():
            try:
                denom_int = int(denom)
                count_int = int(count)
                if denom_int not in self.VALID_DENOMINATIONS:
                    errors.append(f"Invalid denomination: {denom}. Valid values: {self.VALID_DENOMINATIONS}")
                    continue
                if count_int < 0:
                    errors.append(f"Count cannot be negative for denomination ₹{denom}")
                    continue
                value = denom_int * count_int
                total += value
                if count_int > 0:
                    breakdown.append({
                        'denomination': denom_int,
                        'count': count_int,
                        'value': value,
                    })
            except (ValueError, TypeError):
                errors.append(f"Invalid value for denomination {denom}")

        breakdown.sort(key=lambda x: x['denomination'], reverse=True)
        return Response({
            'total': total,
            'formatted_total': f"₹{total:,}",
            'breakdown': breakdown,
            'currency': 'INR',
            'errors': errors if errors else None,
        })
