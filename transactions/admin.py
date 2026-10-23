from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'transaction_type', 'amount', 'category', 'account', 'date', 'user']
    list_filter = ['transaction_type', 'date', 'is_recurring']
    search_fields = ['title', 'description', 'user__email', 'tags']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
