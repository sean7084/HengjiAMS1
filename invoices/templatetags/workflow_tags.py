from django import template

register = template.Library()


BADGE_MAP = {
    'quotation': {
        'draft': 'bg-secondary',
        'sent': 'bg-primary',
        'confirmed': 'bg-success',
        'expired': 'bg-warning text-dark',
        'cancelled': 'bg-danger',
    },
    'delivery': {
        'pending': 'bg-secondary',
        'prepared': 'bg-info text-dark',
        'dispatched': 'bg-primary',
        'completed': 'bg-success',
    },
    'invoice_dispatch': {
        'draft': 'bg-secondary',
        'sent': 'bg-primary',
        'client_confirmed': 'bg-success',
        'esker_forwarded': 'bg-info text-dark',
        'failed': 'bg-danger',
    },
    'purchase': {
        'ordered': 'bg-secondary',
        'receiving': 'bg-primary',
        'complete': 'bg-success',
    },
}


@register.filter
def workflow_badge_class(value, entity_type):
    mapping = BADGE_MAP.get(entity_type, {})
    return mapping.get(str(value), 'bg-secondary')


@register.filter
def quotation_next_action(quotation):
    status = getattr(quotation, 'status', None)
    if status == 'draft':
        return 'Mark as Sent'
    if status == 'sent':
        return 'Confirm Quotation'
    if status == 'confirmed':
        delivery_order = quotation.delivery_orders.order_by('-created_at').first()
        if delivery_order:
            return 'Open Delivery'
        purchase_order = getattr(quotation, 'purchase_order', None)
        if not purchase_order:
            return 'Create Purchase Order'
        if purchase_order.status == 'complete':
            return 'Create Delivery'
        return 'Receive Stock'
    if status == 'expired':
        return 'Duplicate and Re-issue'
    if status == 'cancelled':
        return 'No Action'
    return 'Review'


@register.filter
def delivery_next_action(delivery):
    status = getattr(delivery, 'status', None)
    if status == 'pending':
        return 'Mark Prepared'
    if status == 'prepared':
        return 'Dispatch Delivery'
    if status == 'dispatched':
        if getattr(delivery, 'signed_file', None):
            return 'Mark Completed'
        return 'Upload Signed Copy'
    if status == 'completed':
        return 'Generate / Send Invoice Docs'
    return 'Review'


@register.filter
def invoice_next_action(invoice):
    delivery = getattr(invoice, 'delivery_order', None)
    if not delivery:
        return 'Link Delivery Order'
    items_qs = getattr(invoice, 'items', None)
    if items_qs is not None and not items_qs.exists():
        return 'Recalculate from Delivery'
    return 'Generate Document / Send Email'


@register.filter
def dispatch_next_action(dispatch):
    status = getattr(dispatch, 'status', None)
    if status == 'draft':
        return 'Send Email'
    if status == 'sent':
        return 'Mark Client Confirmed'
    if status == 'client_confirmed':
        return 'Forward to Esker'
    if status == 'esker_forwarded':
        return 'Completed'
    if status == 'failed':
        return 'Retry Send'
    return 'Review'
