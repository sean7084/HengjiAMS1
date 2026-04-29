from django.urls import reverse

from accounts.models import ReceivedEmailMessage
from quotations.models import Quotation


def pending_tasks(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.can_manage_orders():
        return {
            'pending_tasks_total': 0,
            'pending_tasks': [],
        }

    tasks = []

    rfq_drafts = Quotation.objects.filter(
        requires_confirmation=True,
        status=Quotation.QuotationStatus.DRAFT,
        source_email_message__isnull=False,
    ).select_related('source_email_message', 'customer').order_by('-created_at')[:5]
    for quotation in rfq_drafts:
        tasks.append(
            {
                'kind': 'rfq_draft',
                'label': f'{quotation.quotation_number} - {quotation.customer.name}',
                'meta': quotation.source_email_message.subject or quotation.source_email_message.sender or 'RFQ draft pending confirmation',
                'url': reverse('quotations:detail', args=[quotation.pk]),
            }
        )

    mailbox = getattr(user, 'mailbox_settings', None)
    if mailbox:
        likely_rfqs = mailbox.received_messages.filter(
            direction=ReceivedEmailMessage.MessageDirection.INBOX,
            rfq_status=ReceivedEmailMessage.RFQStatus.CLASSIFIED_RFQ,
            linked_quotations__isnull=True,
        ).order_by('-received_at', '-id')[:5]
        for message in likely_rfqs:
            tasks.append(
                {
                    'kind': 'rfq_message',
                    'label': message.subject or message.sender or f'Mailbox Message {message.pk}',
                    'meta': 'Likely RFQ not yet converted',
                    'url': reverse('accounts:mailbox_detail', args=[message.pk]),
                }
            )

        if mailbox.last_connection_status == 'failed':
            tasks.append(
                {
                    'kind': 'mailbox_failure',
                    'label': mailbox.email_address,
                    'meta': mailbox.last_connection_message or 'Mailbox sync failed',
                    'url': reverse('accounts:mailbox_inbox'),
                }
            )

    return {
        'pending_tasks_total': len(tasks),
        'pending_tasks': tasks[:10],
    }