from django.contrib import admin
from .models import SplitExpense, SplitMember


class SplitMemberInline(admin.TabularInline):
    model = SplitMember
    extra = 0
    fields = ['name', 'email', 'share_amount', 'share_percentage', 'is_paid', 'paid_at']
    readonly_fields = ['paid_at']


@admin.register(SplitExpense)
class SplitExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'total_amount', 'status', 'user', 'date', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['title', 'user__email']
    inlines = [SplitMemberInline]
    ordering = ['-date', '-created_at']
