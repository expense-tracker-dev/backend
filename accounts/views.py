from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .models import Account
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    AccountSerializer,
    AccountBalanceUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful. Welcome to MoneyMate!'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user, is_active=True)


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        account.is_active = False
        account.save()
        return Response({'message': 'Account deactivated successfully.'}, status=status.HTTP_200_OK)


class AccountSummaryView(APIView):
    """Returns total balance across all accounts for the user."""

    def get(self, request):
        accounts = Account.objects.filter(user=request.user, is_active=True)
        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or 0
        by_type = {}
        for account in accounts:
            acc_type = account.account_type
            if acc_type not in by_type:
                by_type[acc_type] = {'count': 0, 'balance': 0}
            by_type[acc_type]['count'] += 1
            by_type[acc_type]['balance'] += float(account.balance)
        return Response({
            'total_balance': float(total_balance),
            'currency': request.user.currency,
            'accounts_count': accounts.count(),
            'breakdown_by_type': by_type,
            'accounts': AccountSerializer(accounts, many=True).data,
        })


class AccountBalanceUpdateView(APIView):
    """Manually adjust account balance."""

    def post(self, request, pk):
        account = Account.objects.get(pk=pk, user=request.user)
        serializer = AccountBalanceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        operation = serializer.validated_data['operation']
        if operation == 'add':
            account.balance += amount
        elif operation == 'subtract':
            account.balance -= amount
        elif operation == 'set':
            account.balance = amount
        account.save()
        return Response({
            'message': 'Balance updated successfully.',
            'new_balance': float(account.balance),
            'account': AccountSerializer(account).data,
        })
