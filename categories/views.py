from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Category
from .serializers import CategorySerializer


DEFAULT_INCOME_CATEGORIES = [
    {'name': 'Salary', 'icon': 'work', 'color': '#4CAF50'},
    {'name': 'Freelance', 'icon': 'laptop', 'color': '#8BC34A'},
    {'name': 'Business', 'icon': 'business', 'color': '#009688'},
    {'name': 'Investment', 'icon': 'trending_up', 'color': '#2196F3'},
    {'name': 'Rental Income', 'icon': 'home', 'color': '#3F51B5'},
    {'name': 'Gift', 'icon': 'card_giftcard', 'color': '#9C27B0'},
    {'name': 'Other Income', 'icon': 'attach_money', 'color': '#607D8B'},
]

DEFAULT_EXPENSE_CATEGORIES = [
    {'name': 'Food & Dining', 'icon': 'restaurant', 'color': '#F44336'},
    {'name': 'Travel', 'icon': 'flight', 'color': '#FF9800'},
    {'name': 'Shopping', 'icon': 'shopping_cart', 'color': '#E91E63'},
    {'name': 'Bills & Utilities', 'icon': 'receipt', 'color': '#9C27B0'},
    {'name': 'Entertainment', 'icon': 'movie', 'color': '#673AB7'},
    {'name': 'Health & Medical', 'icon': 'local_hospital', 'color': '#F44336'},
    {'name': 'Education', 'icon': 'school', 'color': '#2196F3'},
    {'name': 'Rent', 'icon': 'house', 'color': '#795548'},
    {'name': 'Transport', 'icon': 'directions_car', 'color': '#FF5722'},
    {'name': 'Groceries', 'icon': 'local_grocery_store', 'color': '#4CAF50'},
    {'name': 'Personal Care', 'icon': 'spa', 'color': '#E91E63'},
    {'name': 'Other Expense', 'icon': 'more_horiz', 'color': '#607D8B'},
]


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = Category.objects.filter(user=self.request.user)
        category_type = self.request.query_params.get('type')
        if category_type:
            queryset = queryset.filter(category_type=category_type)
        return queryset


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class InitializeDefaultCategoriesView(APIView):
    """Create default income and expense categories for a new user."""

    def post(self, request):
        user = request.user
        created_count = 0
        for cat in DEFAULT_INCOME_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                user=user, name=cat['name'], category_type='income',
                defaults={'icon': cat['icon'], 'color': cat['color'], 'is_default': True}
            )
            if created:
                created_count += 1
        for cat in DEFAULT_EXPENSE_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                user=user, name=cat['name'], category_type='expense',
                defaults={'icon': cat['icon'], 'color': cat['color'], 'is_default': True}
            )
            if created:
                created_count += 1
        return Response({
            'message': f'{created_count} default categories created.',
            'total_categories': Category.objects.filter(user=user).count()
        })
