from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'month', 'year', 'alert_threshold', 'created_at']
    list_filter = ['month', 'year']
    search_fields = ['user__email', 'category__name']
    ordering = ['-year', '-month']
