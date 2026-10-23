from django.db import models
from django.conf import settings


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, related_name='transactions')
    category = models.ForeignKey('categories.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    time = models.TimeField(auto_now_add=True)
    # For transfer transactions
    to_account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transfers')
    is_recurring = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, null=True)  # comma-separated tags
    attachment = models.ImageField(upload_to='receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.title} - {self.amount}"

    def save(self, *args, **kwargs):
        """Auto-update account balance on transaction save."""
        is_new = self.pk is None
        if not is_new:
            # Reverse old transaction effect
            old = Transaction.objects.get(pk=self.pk)
            self._reverse_balance(old)
        super().save(*args, **kwargs)
        if is_new:
            self._apply_balance()

    def _apply_balance(self):
        if self.account:
            if self.transaction_type == 'income':
                self.account.balance += self.amount
            elif self.transaction_type == 'expense':
                self.account.balance -= self.amount
            elif self.transaction_type == 'transfer' and self.to_account:
                self.account.balance -= self.amount
                self.to_account.balance += self.amount
                self.to_account.save()
            self.account.save()

    def _reverse_balance(self, old_transaction):
        if old_transaction.account:
            if old_transaction.transaction_type == 'income':
                old_transaction.account.balance -= old_transaction.amount
            elif old_transaction.transaction_type == 'expense':
                old_transaction.account.balance += old_transaction.amount
            elif old_transaction.transaction_type == 'transfer' and old_transaction.to_account:
                old_transaction.account.balance += old_transaction.amount
                old_transaction.to_account.balance -= old_transaction.amount
                old_transaction.to_account.save()
            old_transaction.account.save()

    def delete(self, *args, **kwargs):
        """Reverse balance on delete."""
        self._reverse_balance(self)
        super().delete(*args, **kwargs)
