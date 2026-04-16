"""
Views for Quotations app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import datetime

from companies.models import Company
from customers.models import CustomerProfile
from products.models import ProductPrice
from .models import Quotation, QuotationItem, QuotationAttachment
from .forms import QuotationForm, QuotationItemForm


class QuotationListView(ListView):
    """List view for quotations with filtering."""
    model = Quotation
    template_name = 'quotations/list.html'
    context_object_name = 'quotations'
    paginate_by = 20

    def get_queryset(self):
        queryset = Quotation.objects.select_related('customer', 'customer_profile').all()

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by customer
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(quotation_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(attn__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Quotation.QuotationStatus.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_customer'] = self.request.GET.get('customer', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['customers'] = Company.objects.filter(status='active').order_by('name')
        return context


class QuotationDetailView(DetailView):
    """Detail view for quotation."""
    model = Quotation
    template_name = 'quotations/detail.html'
    context_object_name = 'quotation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['attachments'] = self.object.attachments.all()
        context['purchase_order'] = getattr(self.object, 'purchase_order', None)
        context['email_dispatches'] = self.object.email_dispatches.all().order_by('-created_at')
        return context


class QuotationCreateView(CreateView):
    """Create view for quotation."""
    model = Quotation
    form_class = QuotationForm
    template_name = 'quotations/form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['quotation_date'] = datetime.date.today()
        initial['valid_until'] = datetime.date.today() + datetime.timedelta(days=30)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Company.objects.filter(status='active').order_by('name')
        context['products'] = ProductPrice.objects.filter(is_current=True).select_related('brand', 'model')
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        quotation = form.save(commit=False)

        # Get customer profile for auto-fill
        try:
            profile = quotation.customer.customer_profile
            quotation.customer_profile = profile
            if not quotation.attn:
                quotation.attn = profile.contact_person
            if not quotation.tel:
                quotation.tel = profile.phone
        except CustomerProfile.DoesNotExist:
            pass

        quotation.save()

        # Handle line items from POST
        items_data = self.request.POST.getlist('items')
        for item_data in items_data:
            if not item_data:
                continue

            # Accept both formats:
            # 1) new|<product_price_id>|<quantity>|<user_brand>|<user_name>
            # 2) <product_price_id>|<quantity>|<user_brand>|<user_name>
            parts = item_data.split('|')
            if len(parts) < 4:
                continue

            if parts[0] == 'new' and len(parts) >= 5:
                product_price_id, quantity, user_brand, user_name = parts[1], parts[2], parts[3], parts[4]
            elif parts[0].startswith('item_'):
                # Ignore existing-item payload in create flow.
                continue
            else:
                product_price_id, quantity, user_brand, user_name = parts[0], parts[1], parts[2], parts[3]

            try:
                product_price = ProductPrice.objects.get(pk=product_price_id)
                quantity = int(quantity)
                item = QuotationItem(
                    quotation=quotation,
                    product_price=product_price,
                    quantity=quantity,
                    user_brand=user_brand,
                    user_name=user_name
                )
                item.save()
            except (ProductPrice.DoesNotExist, ValueError):
                pass

        messages.success(self.request, f'Quotation {quotation.quotation_number} created successfully.')
        return HttpResponseRedirect(reverse_lazy('quotations:detail', args=[quotation.pk]))


class QuotationUpdateView(UpdateView):
    """Update view for quotation."""
    model = Quotation
    form_class = QuotationForm
    template_name = 'quotations/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Company.objects.filter(status='active').order_by('name')
        context['products'] = ProductPrice.objects.filter(is_current=True).select_related('brand', 'model')
        context['items'] = self.object.items.all()
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        quotation = form.save()

        # Update line items
        # First, delete removed items
        submitted_ids = set()
        items_data = self.request.POST.getlist('items')

        for item_data in items_data:
            if not item_data:
                continue

            # Existing item: item_<pk>|<product_price_id>|<quantity>|<user_brand>|<user_name>
            # New item: new|<product_price_id>|<quantity>|<user_brand>|<user_name>
            parts = item_data.split('|')
            if len(parts) < 5:
                continue

            marker = parts[0]
            product_price_id, quantity, user_brand, user_name = parts[1], parts[2], parts[3], parts[4]

            try:
                product_price = ProductPrice.objects.get(pk=product_price_id)
                quantity = int(quantity)

                if marker.startswith('item_'):
                    item_pk = marker.replace('item_', '')
                    submitted_ids.add(item_pk)
                    item = QuotationItem.objects.get(pk=item_pk, quotation=quotation)
                    item.product_price = product_price
                    item.quantity = quantity
                    item.user_brand = user_brand
                    item.user_name = user_name
                    item.save()
                elif marker == 'new':
                    item = QuotationItem(
                        quotation=quotation,
                        product_price=product_price,
                        quantity=quantity,
                        user_brand=user_brand,
                        user_name=user_name
                    )
                    item.save()
                    submitted_ids.add(str(item.pk))
            except (ProductPrice.DoesNotExist, QuotationItem.DoesNotExist, ValueError):
                pass

        # Delete items not in submitted list
        for item in quotation.items.all():
            if str(item.pk) not in submitted_ids:
                item.delete()

        messages.success(self.request, f'Quotation {quotation.quotation_number} updated successfully.')
        return HttpResponseRedirect(reverse_lazy('quotations:detail', args=[quotation.pk]))


class QuotationDeleteView(DeleteView):
    """Delete view for quotation."""
    model = Quotation
    template_name = 'quotations/confirm_delete.html'
    success_url = reverse_lazy('quotations:list')

    def form_valid(self, form):
        messages.success(self.request, 'Quotation deleted successfully.')
        return super().form_valid(form)


def generate_quotation_pdf(request, pk):
    """Generate PDF for quotation."""
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.units import mm, inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO

    quotation = get_object_or_404(Quotation, pk=pk)
    items = quotation.items.all()

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12)
    normal_style = styles['Normal']

    elements = []

    # Header
    elements.append(Paragraph('QUOTATION', title_style))
    elements.append(Spacer(1, 10*mm))

    # Quotation Info Table
    info_data = [
        ['Quotation Number:', quotation.quotation_number],
        ['Date:', quotation.quotation_date.strftime('%Y-%m-%d')],
        ['Valid Until:', quotation.valid_until.strftime('%Y-%m-%d')],
        ['Status:', quotation.get_status_display()],
    ]

    if quotation.customer:
        info_data.append(['Customer:', quotation.customer.name])

    if quotation.attn:
        info_data.append(['Attn:', quotation.attn])

    if quotation.tel:
        info_data.append(['Tel:', quotation.tel])

    info_table = Table(info_data, colWidths=[50*mm, 120*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15*mm))

    # Items Table
    elements.append(Paragraph('Items', heading_style))

    items_data = [['#', 'Brand', 'Description', 'User Brand', 'User', 'Unit', 'Qty', 'Unit Price', 'Amount']]
    for idx, item in enumerate(items, 1):
        items_data.append([
            str(idx),
            item.brand_name[:20],
            item.product_description[:40] if item.product_description else '',
            item.user_brand[:20] if item.user_brand else '',
            item.user_name[:20] if item.user_name else '',
            item.unit,
            str(item.quantity),
            f'¥{item.unit_price:,.2f}',
            f'¥{item.line_total_without_tax:,.2f}',
        ])

    items_table = Table(items_data, colWidths=[10*mm, 25*mm, 45*mm, 25*mm, 25*mm, 15*mm, 12*mm, 25*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (4, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 10*mm))

    # Totals
    totals_data = [
        ['Subtotal (excl. tax):', f'¥{quotation.total_without_tax:,.2f}'],
        ['Tax:', f'¥{quotation.total_tax:,.2f}'],
        ['Total (incl. tax):', f'¥{quotation.total_with_tax:,.2f}'],
    ]
    totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(totals_table)

    # Notes
    if quotation.notes:
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph('Notes:', heading_style))
        elements.append(Paragraph(quotation.notes, normal_style))

    # Build PDF
    doc.build(elements)

    # Return PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quotation.quotation_number}.pdf"'
    return response


def duplicate_quotation(request, pk):
    """Duplicate an existing quotation."""
    original = get_object_or_404(Quotation, pk=pk)

    with transaction.atomic():
        # Create new quotation
        new_quotation = Quotation(
            customer=original.customer,
            customer_profile=original.customer_profile,
            quotation_date=datetime.date.today(),
            valid_until=datetime.date.today() + datetime.timedelta(days=30),
            attn=original.attn,
            tel=original.tel,
            status=Quotation.QuotationStatus.DRAFT,
            notes=original.notes,
        )
        new_quotation.save()

        # Copy items
        for item in original.items.all():
            new_item = QuotationItem(
                quotation=new_quotation,
                product_price=item.product_price,
                brand_name=item.brand_name,
                product_description=item.product_description,
                model_number=item.model_number,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=item.tax_rate,
                user_brand=item.user_brand,
                user_name=item.user_name,
            )
            new_item.save()

    messages.success(request, f'Quotation duplicated as {new_quotation.quotation_number}.')
    return HttpResponseRedirect(reverse_lazy('quotations:detail', args=[new_quotation.pk]))


def cancel_quotation(request, pk):
    """Cancel a quotation."""
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = Quotation.QuotationStatus.CANCELLED
    quotation.save()
    messages.success(request, f'Quotation {quotation.quotation_number} cancelled.')
    return redirect(reverse_lazy('quotations:detail', args=[quotation.pk]))


def confirm_quotation(request, pk):
    """Mark quotation as confirmed."""
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = Quotation.QuotationStatus.CONFIRMED
    quotation.save()
    messages.success(request, f'Quotation {quotation.quotation_number} confirmed.')
    return redirect(reverse_lazy('quotations:detail', args=[quotation.pk]))


def send_quotation(request, pk):
    """Mark quotation as sent."""
    quotation = get_object_or_404(Quotation, pk=pk)
    quotation.status = Quotation.QuotationStatus.SENT
    quotation.save()
    messages.success(request, f'Quotation {quotation.quotation_number} marked as sent.')
    return redirect(reverse_lazy('quotations:detail', args=[quotation.pk]))


def attachment_upload(request, pk):
    """Upload attachment to quotation."""
    quotation = get_object_or_404(Quotation, pk=pk)

    if request.method == 'POST':
        attachment_type = request.POST.get('attachment_type')
        file = request.FILES.get('file')
        notes = request.POST.get('notes', '')

        if not file:
            messages.error(request, 'No file provided.')
            return redirect(reverse_lazy('quotations:detail', args=[pk]))

        # Validate file type
        allowed_extensions = ['.pdf', '.ofd', '.zip']
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            messages.error(request, f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
            return redirect(reverse_lazy('quotations:detail', args=[pk]))

        # Create attachment
        attachment = QuotationAttachment(
            quotation=quotation,
            attachment_type=attachment_type,
            file=file,
            notes=notes
        )
        attachment.save()

        messages.success(request, 'Attachment uploaded successfully.')

    return redirect(reverse_lazy('quotations:detail', args=[pk]))


def attachment_delete(request, pk):
    """Delete an attachment."""
    attachment = get_object_or_404(QuotationAttachment, pk=pk)
    quotation_pk = attachment.quotation.pk

    if request.method == 'POST':
        attachment.file.delete()
        attachment.delete()
        messages.success(request, 'Attachment deleted.')

    return redirect(reverse_lazy('quotations:detail', args=[quotation_pk]))


def convert_to_purchase(request, pk):
    """Convert confirmed quotation to purchase order records."""
    quotation = get_object_or_404(Quotation, pk=pk)

    if quotation.status != Quotation.QuotationStatus.CONFIRMED:
        messages.error(request, 'Only confirmed quotations can be converted to purchase.')
        return redirect(reverse_lazy('quotations:detail', args=[pk]))

    if request.method == 'POST':
        from purchases.models import PurchaseOrder, PurchaseOrderItem

        created_items = 0

        with transaction.atomic():
            purchase_order, created = PurchaseOrder.objects.get_or_create(
                quotation=quotation,
                defaults={
                    'status': PurchaseOrder.Status.ORDERED,
                }
            )

            for item in quotation.items.all():
                _, item_created = PurchaseOrderItem.objects.get_or_create(
                    purchase_order=purchase_order,
                    quotation_item=item,
                    defaults={
                        'product_price': item.product_price,
                        'brand': item.product_price.brand if item.product_price else None,
                        'model': item.product_price.model if item.product_price else None,
                        'product_description': item.product_description,
                        'unit': item.unit,
                        'quantity_ordered': item.quantity,
                        'unit_price': item.unit_price,
                    }
                )
                if item_created:
                    created_items += 1

            purchase_order.recalculate_progress()

        if created_items:
            messages.success(request, f'Created purchase order {purchase_order.po_number} with {created_items} line(s).')
        elif created:
            messages.warning(request, f'Purchase order {purchase_order.po_number} was created without lines.')
        else:
            messages.info(request, f'Purchase order {purchase_order.po_number} already exists. You can continue receiving stock.')

        return redirect(reverse_lazy('purchases:receive', args=[purchase_order.pk]))

    # Show confirmation page
    purchase_order = getattr(quotation, 'purchase_order', None)
    return render(request, 'quotations/convert_confirm.html', {
        'quotation': quotation,
        'total_items': sum(item.quantity for item in quotation.items.all()),
        'purchase_order': purchase_order,
    })
