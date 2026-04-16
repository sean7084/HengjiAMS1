from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from deliveries.models import DeliveryItem, DeliveryOrder
from purchases.models import PurchaseOrder
from quotations.models import Quotation

from .models import EmailDispatch, InvoiceInfo, WorkflowStatusAudit
from .services import recalculate_invoice_from_delivery


def _log_status_change(instance, entity_type, reference, old_status, new_status):
    if old_status == new_status:
        return

    WorkflowStatusAudit.objects.create(
        entity_type=entity_type,
        entity_id=str(instance.pk),
        reference=reference,
        from_status=old_status or '',
        to_status=new_status or '',
    )


@receiver(pre_save, sender=Quotation)
def audit_quotation_status_change(sender, instance, **kwargs):
    old_status = None
    if instance.pk:
        old = Quotation.objects.filter(pk=instance.pk).only('status', 'quotation_number').first()
        old_status = old.status if old else None
    _log_status_change(instance, 'quotation', instance.quotation_number or '', old_status, instance.status)


@receiver(pre_save, sender=PurchaseOrder)
def audit_purchase_status_change(sender, instance, **kwargs):
    old_status = None
    if instance.pk:
        old = PurchaseOrder.objects.filter(pk=instance.pk).only('status', 'po_number').first()
        old_status = old.status if old else None
    _log_status_change(instance, 'purchase_order', instance.po_number or '', old_status, instance.status)


@receiver(pre_save, sender=DeliveryOrder)
def audit_delivery_status_change(sender, instance, **kwargs):
    old_status = None
    if instance.pk:
        old = DeliveryOrder.objects.filter(pk=instance.pk).only('status', 'delivery_number').first()
        old_status = old.status if old else None
    _log_status_change(instance, 'delivery_order', instance.delivery_number or '', old_status, instance.status)


@receiver(pre_save, sender=EmailDispatch)
def audit_email_dispatch_status_change(sender, instance, **kwargs):
    old_status = None
    if instance.pk:
        old = EmailDispatch.objects.filter(pk=instance.pk).only('status').first()
        old_status = old.status if old else None
    _log_status_change(instance, 'email_dispatch', instance.subject or '', old_status, instance.status)


@receiver(post_save, sender=InvoiceInfo)
def audit_invoice_created(sender, instance, created, **kwargs):
    if created:
        WorkflowStatusAudit.objects.create(
            entity_type='invoice_info',
            entity_id=str(instance.pk),
            reference=instance.invoice_number,
            from_status='',
            to_status='created',
        )


@receiver(post_save, sender=DeliveryItem)
def recalculate_linked_invoices_on_delivery_item_save(sender, instance, **kwargs):
    linked_invoices = InvoiceInfo.objects.filter(delivery_order=instance.delivery_order)
    for invoice in linked_invoices:
        recalculate_invoice_from_delivery(invoice)


@receiver(post_delete, sender=DeliveryItem)
def recalculate_linked_invoices_on_delivery_item_delete(sender, instance, **kwargs):
    linked_invoices = InvoiceInfo.objects.filter(delivery_order=instance.delivery_order)
    for invoice in linked_invoices:
        recalculate_invoice_from_delivery(invoice)
