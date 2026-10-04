from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InvoiceLineItem, Invoice, Payment
from finance.helpers_accounting import create_journal_entry_from_invoice, create_journal_entry_from_payment

@receiver(post_save, sender=InvoiceLineItem)
def auto_decrement_inventory(sender, instance, created, **kwargs):
    """
    When an invoice line item is created, decrement the stock of the associated product.
    """
    if created and instance.product:
        instance.product.quantity_on_hand -= instance.quantity
        instance.product.save(update_fields=['quantity_on_hand'])


@receiver(post_save, sender=Payment)
def create_payment_journal(sender, instance, created, **kwargs):
    """
    When a Payment is recorded, create a Journal Entry for Cash received.
    """
    if created:
        create_journal_entry_from_payment(instance)
