from django.db import models
from django.conf import settings


class SplitExpense(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('settled', 'Settled'),
        ('partial', 'Partially Settled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='split_expenses')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.total_amount}"


class SplitMember(models.Model):
    split_expense = models.ForeignKey(SplitExpense, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    share_amount = models.DecimalField(max_digits=15, decimal_places=2)
    share_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.share_amount}"
