"""Views for delivery order workflow."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from assets.models import Asset
from quotations.models import Quotation

from .forms import DeliveryOrderForm, SignedCopyUploadForm
from .models import DeliveryItem, DeliveryOrder
from .services import render_delivery_pdf_html


class OrderManagementAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_orders()

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')


class DeliveryOrderListView(OrderManagementAccessMixin, ListView):
    """List deliveries with filtering and search."""

    model = DeliveryOrder
    template_name = 'deliveries/list.html'
    context_object_name = 'deliveries'
    paginate_by = 20

    def get_queryset(self):
        queryset = DeliveryOrder.objects.select_related('quotation', 'quotation__customer').all()

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            queryset = queryset.filter(quotation_id=quotation_id)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(delivery_number__icontains=search)
                | Q(quotation__quotation_number__icontains=search)
                | Q(quotation__customer__name__icontains=search)
                | Q(receiver_name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = DeliveryOrder.Status.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_quotation'] = self.request.GET.get('quotation', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['quotations'] = Quotation.objects.filter(delivery_orders__isnull=False).distinct().order_by('-created_at')
        return context


class DeliveryOrderDetailView(OrderManagementAccessMixin, DetailView):
    """Detail page for a delivery order."""

    model = DeliveryOrder
    template_name = 'deliveries/detail.html'
    context_object_name = 'delivery'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('asset').all()
        context['upload_form'] = SignedCopyUploadForm(instance=self.object)
        return context


def delivery_create_view(request, quotation_pk):
    """Create delivery order from a quotation and select dispatch assets."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    quotation = get_object_or_404(
        Quotation.objects.select_related('customer', 'customer__primary_contact_company_user__user'),
        pk=quotation_pk,
    )

    available_assets = Asset.objects.filter(
        source_quotation=quotation,
        status=Asset.AssetStatus.AVAILABLE,
    ).select_related('brand', 'model').order_by('asset_number')

    if not available_assets.exists():
        messages.error(request, 'No available assets found for this quotation.')
        return redirect(reverse('purchases:stock'))

    initial_data = {
        'delivery_date': quotation.quotation_date,
        'delivery_method': '',
        'receiver_name': quotation.attn,
        'receiver_phone': quotation.tel,
    }

    primary_location = quotation.customer.locations.order_by('name').first()
    if primary_location:
        initial_data['delivery_address'] = primary_location.get_full_address()

    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST, quotation=quotation)
        if form.is_valid():
            try:
                with transaction.atomic():
                    delivery = form.save(commit=False)
                    delivery.quotation = quotation
                    delivery.save()

                    selected_assets = form.cleaned_data['selected_assets']
                    for asset in selected_assets:
                        DeliveryItem.objects.create(
                            delivery_order=delivery,
                            asset=asset,
                            quantity=1,
                        )
            except ValidationError as exc:
                form.add_error('selected_assets', '; '.join(exc.messages))
            else:
                messages.success(request, f'Delivery order {delivery.delivery_number} created.')
                return redirect('deliveries:detail', pk=delivery.pk)
    else:
        form = DeliveryOrderForm(initial=initial_data, quotation=quotation)

    return render(
        request,
        'deliveries/form.html',
        {
            'form': form,
            'quotation': quotation,
            'available_assets': available_assets,
        },
    )


def mark_prepared(request, pk):
    """Mark delivery as prepared."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    if request.method != 'POST':
        messages.warning(request, 'Invalid request method.')
        return redirect('deliveries:detail', pk=pk)

    delivery = get_object_or_404(DeliveryOrder, pk=pk)
    if delivery.status != DeliveryOrder.Status.PENDING:
        messages.warning(request, 'Only pending deliveries can be marked prepared.')
        return redirect('deliveries:detail', pk=pk)

    delivery.status = DeliveryOrder.Status.PREPARED
    delivery.save(update_fields=['status', 'updated_at'])
    messages.success(request, f'{delivery.delivery_number} is now prepared.')
    return redirect('deliveries:detail', pk=pk)


def mark_dispatched(request, pk):
    """Dispatch delivery and update linked asset statuses."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    if request.method != 'POST':
        messages.warning(request, 'Invalid request method.')
        return redirect('deliveries:detail', pk=pk)

    delivery = get_object_or_404(DeliveryOrder.objects.prefetch_related('items__asset'), pk=pk)
    if delivery.status not in {DeliveryOrder.Status.PENDING, DeliveryOrder.Status.PREPARED}:
        messages.warning(request, 'Only pending or prepared deliveries can be dispatched.')
        return redirect('deliveries:detail', pk=pk)

    for item in delivery.items.all():
        if item.asset.status != Asset.AssetStatus.AVAILABLE:
            messages.error(
                request,
                f"Asset {item.asset.asset_number} is not available for dispatch.",
            )
            return redirect('deliveries:detail', pk=pk)

    with transaction.atomic():
        for item in delivery.items.all():
            asset = item.asset
            asset.status = Asset.AssetStatus.ASSIGNED
            asset.save(update_fields=['status', 'updated_at'])

        delivery.status = DeliveryOrder.Status.DISPATCHED
        delivery.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'{delivery.delivery_number} dispatched successfully.')
    return redirect('deliveries:detail', pk=pk)


def upload_signed_copy(request, pk):
    """Upload signed delivery copy."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    if request.method != 'POST':
        messages.warning(request, 'Invalid request method.')
        return redirect('deliveries:detail', pk=pk)

    delivery = get_object_or_404(DeliveryOrder, pk=pk)

    if request.method == 'POST':
        form = SignedCopyUploadForm(request.POST, request.FILES, instance=delivery)
        if form.is_valid():
            form.save()
            messages.success(request, 'Signed copy uploaded successfully.')
        else:
            messages.error(request, '; '.join(form.errors.get('signed_file', ['Invalid file.'])))

    return redirect('deliveries:detail', pk=pk)


def mark_completed(request, pk):
    """Complete delivery and set linked assets to in-use."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    if request.method != 'POST':
        messages.warning(request, 'Invalid request method.')
        return redirect('deliveries:detail', pk=pk)

    delivery = get_object_or_404(DeliveryOrder.objects.prefetch_related('items__asset'), pk=pk)
    if delivery.status != DeliveryOrder.Status.DISPATCHED:
        messages.warning(request, 'Only dispatched deliveries can be completed.')
        return redirect('deliveries:detail', pk=pk)

    if not delivery.signed_file:
        messages.error(request, 'Please upload signed copy before completing delivery.')
        return redirect('deliveries:detail', pk=pk)

    with transaction.atomic():
        for item in delivery.items.all():
            asset = item.asset
            asset.status = Asset.AssetStatus.IN_USE
            asset.save(update_fields=['status', 'updated_at'])

        delivery.status = DeliveryOrder.Status.COMPLETED
        delivery.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'{delivery.delivery_number} marked as completed.')
    return redirect('deliveries:detail', pk=pk)


def generate_delivery_pdf(request, pk):
    """Generate delivery document from HTML template and return PDF."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')

    delivery = get_object_or_404(DeliveryOrder.objects.prefetch_related('items'), pk=pk)

    try:
        pdf_bytes = render_delivery_pdf_html(delivery)
    except Exception as exc:
        messages.error(request, f'Failed to generate delivery PDF: {exc}')
        return redirect('deliveries:detail', pk=pk)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="{delivery.delivery_number}.pdf"'
    )
    return response
