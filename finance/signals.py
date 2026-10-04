"""
Finance Signals — Auto-create journal entries when Income/Expense are created.

This bridges the existing single-entry Income/Expense models with the new
double-entry accounting system. When an Income or Expense is saved, a
corresponding journal entry is automatically created and posted.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Income, Expense
from .helpers_accounting import (
    create_journal_entry_from_income,
    create_journal_entry_from_expense,
)


@receiver(post_save, sender=Income)
def auto_journal_from_income(sender, instance, created, **kwargs):
    """
    When a new Income record is created, automatically generate a
    double-entry journal entry:
        Debit: Cash/Bank
        Credit: Revenue account
    """
    if created:
        try:
            create_journal_entry_from_income(instance)
        except Exception:
            # Don't block income creation if journal fails
            # (e.g., chart of accounts not yet seeded)
            pass


@receiver(post_save, sender=Expense)
def auto_journal_from_expense(sender, instance, created, **kwargs):
    """
    When a new Expense record is created, automatically generate a
    double-entry journal entry:
        Debit: Expense account
        Credit: Cash/Bank
    """
    if created:
        try:
            create_journal_entry_from_expense(instance)
        except Exception:
            pass

        # Inventory logic: If it's a stock expense, increment product quantity
        if instance.expense_type == 'STOCK' and instance.product:
            instance.product.quantity_on_hand += instance.amount / instance.product.cost_price if instance.product.cost_price else 1
            # Actually, the user just specifies an amount for the expense. 
            # We should probably increment by quantity. Since Expense doesn't have a quantity field,
            # we can derive quantity = amount / cost_price. Or default to 1 if cost_price is 0.
            qty = (instance.amount / instance.product.cost_price) if instance.product.cost_price and instance.product.cost_price > 0 else 1
            instance.product.quantity_on_hand += qty
            instance.product.save(update_fields=['quantity_on_hand'])

