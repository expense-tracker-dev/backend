from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Account


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'phone_number', 'currency', 'is_active', 'created_at']
    list_filter = ['is_active', 'currency', 'is_staff']
    search_fields = ['email', 'username', 'phone_number']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('MoneyMate Info', {'fields': ('phone_number', 'profile_picture', 'currency')}),
    )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'account_type', 'balance', 'currency', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active', 'currency']
    search_fields = ['user__email', 'name']
    ordering = ['-created_at']
