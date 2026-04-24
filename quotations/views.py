"""
Views for Quotations app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from decimal import Decimal, InvalidOperation
import datetime

from companies.models import Company, CompanyUser
from products.models import ProductPrice
from .models import Quotation, QuotationItem, QuotationAttachment
from .forms import QuotationForm, QuotationItemForm
from .services import render_quotation_pdf_html


class OrderManagementAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_orders()

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')


def _normalize_name(name):
    return ' '.join((name or '').split()).strip()


def _get_membership_user_name(membership):
    user = getattr(membership, 'user', None)
    if not user:
        return ''
    return _normalize_name(user.get_display_name() or user.get_full_name())


def _get_membership_user_phone(membership):
    user = getattr(membership, 'user', None)
    return membership.work_phone or getattr(user, 'phone_number', '') or ''


def _find_company_user_by_name(company, name):
    target = _normalize_name(name).lower()
    if not target:
        return None

    memberships = company.company_users.select_related('user').all()
    for membership in memberships:
        user = getattr(membership, 'user', None)
        if not user:
            continue
        display_name = _normalize_name(user.get_display_name()).lower()
        full_name = _normalize_name(user.get_full_name()).lower()
        if target == display_name or (full_name and target == full_name):
            return membership
    return None


def _split_name(full_name):
    parts = _normalize_name(full_name).split()
    if not parts:
        return '', ''
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], ' '.join(parts[1:])


def _create_company_user(company, full_name, phone=''):
    UserModel = get_user_model()
    first_name, last_name = _split_name(full_name)

    base = slugify(full_name) or 'user'
    candidate = f'auto_{base}'
    suffix = 1
    while UserModel.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f'auto_{base}_{suffix}'

    user = UserModel(
        username=candidate[:150],
        first_name=first_name[:150],
        last_name=last_name[:150],
        phone_number=(phone or '')[:20],
        company=company,
    )
    user.set_unusable_password()
    user.save()

    membership = CompanyUser.objects.create(
        user=user,
        company=company,
        role=CompanyUser.CompanyRole.EMPLOYEE,
        status=CompanyUser.UserStatus.ACTIVE,
        work_phone=(phone or '')[:20],
    )
    return membership


def _ensure_company_user(company, full_name, phone=''):
    normalized = _normalize_name(full_name)
    if not normalized:
        return None, False

    existing = _find_company_user_by_name(company, normalized)
    if existing:
        return existing, False
    return _create_company_user(company, normalized, phone), True


def _build_customer_user_context(customers):
    company_users_by_customer = {}
    for customer in customers:
        seen = set()
        users = []
        for membership in customer.company_users.select_related('user').all():
            name = _get_membership_user_name(membership)
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            users.append({
                'name': name,
                'phone': _get_membership_user_phone(membership),
            })
        company_users_by_customer[str(customer.pk)] = users

    company_codes = list(
        Company.objects.filter(status=Company.CompanyStatus.ACTIVE)
        .exclude(code='')
        .order_by('code')
        .values_list('code', flat=True)
        .distinct()
    )

    return company_users_by_customer, company_codes


class QuotationListView(OrderManagementAccessMixin, ListView):
    """List view for quotations with filtering."""
    model = Quotation
    template_name = 'quotations/list.html'
    context_object_name = 'quotations'
    paginate_by = 20

    def get_queryset(self):
        queryset = Quotation.objects.select_related('customer').all()

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


class QuotationDetailView(OrderManagementAccessMixin, DetailView):
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


class QuotationCreateView(OrderManagementAccessMixin, CreateView):
    """Create view for quotation."""
    model = Quotation
    form_class = QuotationForm
    template_name = 'quotations/form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['quotation_date'] = datetime.date.today()
        initial['valid_until'] = datetime.date.today() + datetime.timedelta(days=30)
        initial['status'] = Quotation.QuotationStatus.SENT
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customers = Company.objects.filter(status='active').select_related('primary_contact_company_user__user').prefetch_related('company_users__user').order_by('name')
        company_users_by_customer, company_codes = _build_customer_user_context(customers)
        context['customers'] = customers
        context['products'] = ProductPrice.objects.filter(is_current=True).select_related('brand', 'model').order_by('brand__name', 'model__name')
        context['company_users_by_customer'] = company_users_by_customer
        context['company_codes'] = company_codes
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        quotation = form.save(commit=False)

        if not quotation.status:
            quotation.status = Quotation.QuotationStatus.SENT

        company_user, created = _ensure_company_user(
            quotation.customer,
            quotation.attn,
            quotation.tel,
        )
        if company_user:
            resolved_name = _get_membership_user_name(company_user)
            if resolved_name:
                quotation.attn = resolved_name
            resolved_phone = _get_membership_user_phone(company_user)
            if resolved_phone:
                quotation.tel = resolved_phone

        contact = quotation.customer.primary_contact_company_user
        if contact:
            if not quotation.attn:
                quotation.attn = _get_membership_user_name(contact)
            if not quotation.tel:
                quotation.tel = _get_membership_user_phone(contact)

        quotation.save()

        # Handle line items from POST
        items_data = self.request.POST.getlist('items')
        for item_data in items_data:
            if not item_data:
                continue

            # Accept both formats:
            # 1) new|<product_price_id>|<quantity>|<user_brand>|<user_name>|<unit_price>|<tax_rate>
            # 2) <product_price_id>|<quantity>|<user_brand>|<user_name>
            parts = item_data.split('|')
            if len(parts) < 4:
                continue

            if parts[0] == 'new' and len(parts) >= 5:
                product_price_id, quantity, user_brand, user_name = parts[1], parts[2], parts[3], parts[4]
                unit_price = parts[5] if len(parts) > 5 else None
                tax_rate = parts[6] if len(parts) > 6 else None
            elif parts[0].startswith('item_'):
                # Ignore existing-item payload in create flow.
                continue
            else:
                product_price_id, quantity, user_brand, user_name = parts[0], parts[1], parts[2], parts[3]
                unit_price = None
                tax_rate = None

            try:
                product_price = ProductPrice.objects.get(pk=product_price_id)
                quantity = int(quantity)
                if user_name:
                    _ensure_company_user(quotation.customer, user_name, '')
                item = QuotationItem(
                    quotation=quotation,
                    product_price=product_price,
                    quantity=quantity,
                    user_brand=user_brand or quotation.customer.code,
                    user_name=user_name
                )
                if unit_price:
                    item.unit_price = Decimal(unit_price)
                if tax_rate:
                    item.tax_rate = Decimal(tax_rate)
                item.save()
            except (ProductPrice.DoesNotExist, ValueError, InvalidOperation):
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
        customers = Company.objects.filter(status='active').select_related('primary_contact_company_user__user').prefetch_related('company_users__user').order_by('name')
        company_users_by_customer, company_codes = _build_customer_user_context(customers)
        context['customers'] = customers
        context['products'] = ProductPrice.objects.filter(is_current=True).select_related('brand', 'model').order_by('brand__name', 'model__name')
        context['company_users_by_customer'] = company_users_by_customer
        context['company_codes'] = company_codes
        context['items'] = self.object.items.all()
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        quotation = form.save()

        company_user, created = _ensure_company_user(
            quotation.customer,
            quotation.attn,
            quotation.tel,
        )
        if company_user:
            resolved_name = _get_membership_user_name(company_user)
            if resolved_name:
                quotation.attn = resolved_name
            resolved_phone = _get_membership_user_phone(company_user)
            if resolved_phone:
                quotation.tel = resolved_phone
            quotation.save(update_fields=['attn', 'tel', 'updated_at'])

        # Update line items
        # First, delete removed items
        submitted_ids = set()
        items_data = self.request.POST.getlist('items')

        for item_data in items_data:
            if not item_data:
                continue

            # Existing item: item_<pk>|<product_price_id>|<quantity>|<user_brand>|<user_name>|<unit_price>|<tax_rate>
            # New item: new|<product_price_id>|<quantity>|<user_brand>|<user_name>|<unit_price>|<tax_rate>
            parts = item_data.split('|')
            if len(parts) < 5:
                continue

            marker = parts[0]
            product_price_id, quantity, user_brand, user_name = parts[1], parts[2], parts[3], parts[4]
            unit_price = parts[5] if len(parts) > 5 else None
            tax_rate = parts[6] if len(parts) > 6 else None

            try:
                product_price = ProductPrice.objects.get(pk=product_price_id)
                quantity = int(quantity)

                if marker.startswith('item_'):
                    item_pk = marker.replace('item_', '')
                    submitted_ids.add(item_pk)
                    item = QuotationItem.objects.get(pk=item_pk, quotation=quotation)
                    if user_name:
                        _ensure_company_user(quotation.customer, user_name, '')
                    item.product_price = product_price
                    item.quantity = quantity
                    item.user_brand = user_brand or quotation.customer.code
                    item.user_name = user_name
                    if unit_price:
                        item.unit_price = Decimal(unit_price)
                    if tax_rate:
                        item.tax_rate = Decimal(tax_rate)
                    item.save()
                elif marker == 'new':
                    if user_name:
                        _ensure_company_user(quotation.customer, user_name, '')
                    item = QuotationItem(
                        quotation=quotation,
                        product_price=product_price,
                        quantity=quantity,
                        user_brand=user_brand or quotation.customer.code,
                        user_name=user_name,
                    )
                    if unit_price:
                        item.unit_price = Decimal(unit_price)
                    if tax_rate:
                        item.tax_rate = Decimal(tax_rate)
                    item.save()
                    submitted_ids.add(str(item.pk))
            except (ProductPrice.DoesNotExist, QuotationItem.DoesNotExist, ValueError, InvalidOperation):
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
    """Generate PDF for quotation using HTML template rendering."""
    quotation = get_object_or_404(Quotation, pk=pk)
    try:
        pdf_bytes = render_quotation_pdf_html(quotation)
    except Exception:
        messages.error(request, 'Quotation PDF generation failed. Please verify HTML template and WeasyPrint runtime dependencies.')
        return redirect(reverse_lazy('quotations:detail', args=[quotation.pk]))

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quotation.quotation_number}.pdf"'
    return response


def duplicate_quotation(request, pk):
    """Duplicate an existing quotation."""
    original = get_object_or_404(Quotation, pk=pk)

    with transaction.atomic():
        # Create new quotation
        new_quotation = Quotation(
            customer=original.customer,
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
