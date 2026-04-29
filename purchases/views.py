"""
Views for Purchases app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
import uuid

from assets.models import Asset
from companies.models import Location
from quotations.models import Quotation
from .models import PurchaseOrder, PurchaseReceipt


INTERNAL_WAREHOUSE_LOCATION_ID = 3


class OrderManagementAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_orders()

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')


class PurchaseListView(OrderManagementAccessMixin, ListView):
    """List view for purchase orders created from quotations."""
    model = PurchaseOrder
    template_name = 'purchases/list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('quotation', 'quotation__customer').prefetch_related('quotation__delivery_orders').all()

        # Filter by quotation
        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            queryset = queryset.filter(quotation_id=quotation_id)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(po_number__icontains=search) |
                Q(quotation__quotation_number__icontains=search) |
                Q(quotation__customer__name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = PurchaseOrder.Status.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_quotation'] = self.request.GET.get('quotation', '')
        context['quotations'] = Quotation.objects.filter(
            purchase_order__isnull=False
        ).distinct().order_by('-created_at')
        for purchase_order in context['purchase_orders']:
            purchase_order.current_delivery_order = purchase_order.quotation.delivery_orders.order_by('-created_at').first()
        return context


class PurchaseDetailView(OrderManagementAccessMixin, DetailView):
    """Detail view for a purchased asset."""
    model = Asset
    template_name = 'purchases/detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.source_quotation:
            context['quotation'] = self.object.source_quotation
        return context


def edit_asset_serial(request, pk):
    """Update serial number for an asset."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        new_serial = request.POST.get('serial_number', '').strip()
        asset.serial_number = new_serial
        asset.save()
        messages.success(request, f'Serial number updated for {asset.asset_number}')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'serial': new_serial})

        return redirect('purchases:detail', pk=pk)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def purchase_receipt_view(request, pk):
    """Receive stock for a purchase order and create linked assets."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')
    purchase_order = get_object_or_404(
        PurchaseOrder.objects.select_related('quotation', 'quotation__customer'),
        pk=pk,
    )
    items = list(purchase_order.items.select_related('brand', 'model', 'product_price', 'quotation_item'))

    if not items:
        messages.error(request, 'This purchase order has no items to receive.')
        return redirect(reverse('quotations:detail', args=[purchase_order.quotation.pk]))

    available_locations = Location.objects.filter(pk=INTERNAL_WAREHOUSE_LOCATION_ID, status='active').order_by('name')

    if not available_locations.exists():
        messages.error(request, 'The internal warehouse location is not available for receipts.')
        return redirect(reverse('quotations:detail', args=[purchase_order.quotation.pk]))

    if request.method == 'POST':
        location_id = request.POST.get('location')
        received_by = request.POST.get('received_by', '').strip() or getattr(request.user, 'username', 'system')
        notes = request.POST.get('notes', '').strip()

        if not location_id:
            messages.error(request, 'Please select a receipt location.')
            return render(request, 'purchases/receipt.html', {
                'purchase_order': purchase_order,
                'items': items,
                'locations': available_locations,
            })

        location = get_object_or_404(available_locations, pk=location_id)

        receive_rows = []
        total_to_receive = 0

        for item in items:
            qty_value = request.POST.get(f'qty_{item.pk}', '0').strip() or '0'
            serials_raw = request.POST.get(f'serials_{item.pk}', '').strip()
            try:
                qty = int(qty_value)
            except ValueError:
                messages.error(request, f'Invalid quantity for item #{item.pk}.')
                return render(request, 'purchases/receipt.html', {
                    'purchase_order': purchase_order,
                    'items': items,
                    'locations': available_locations,
                })

            if qty < 0:
                messages.error(request, f'Quantity cannot be negative for item #{item.pk}.')
                return render(request, 'purchases/receipt.html', {
                    'purchase_order': purchase_order,
                    'items': items,
                    'locations': available_locations,
                })

            if qty > item.quantity_remaining:
                messages.error(request, f'Cannot receive more than remaining quantity for item #{item.pk}.')
                return render(request, 'purchases/receipt.html', {
                    'purchase_order': purchase_order,
                    'items': items,
                    'locations': available_locations,
                })

            if qty == 0:
                continue

            serials = [s.strip() for s in serials_raw.replace(',', '\n').splitlines() if s.strip()]
            if len(serials) != qty:
                messages.error(request, f'Provide exactly {qty} serial number(s) for item #{item.pk}.')
                return render(request, 'purchases/receipt.html', {
                    'purchase_order': purchase_order,
                    'items': items,
                    'locations': available_locations,
                })

            receive_rows.append((item, qty, serials))
            total_to_receive += qty

        if total_to_receive == 0:
            messages.warning(request, 'No quantities entered for receipt.')
            return render(request, 'purchases/receipt.html', {
                'purchase_order': purchase_order,
                'items': items,
                'locations': available_locations,
            })

        with transaction.atomic():
            from assets.models import AssetCategory

            category, _ = AssetCategory.objects.get_or_create(
                code='PURCHASED',
                defaults={
                    'name': 'Purchased Items',
                    'description': 'Items purchased via quotation workflow',
                },
            )

            receipt = PurchaseReceipt.objects.create(
                quotation=purchase_order.quotation,
                purchase_order=purchase_order,
                receipt_date=timezone.localdate(),
                received_by=received_by,
                location=location,
                received_count=total_to_receive,
                notes=notes,
            )

            created_assets = 0
            for item, qty, serials in receive_rows:
                for serial in serials:
                    asset = Asset(
                        category=category,
                        brand=item.brand,
                        model=item.model,
                        description=item.product_description,
                        serial_number=serial,
                        barcode=f'RCPT-{uuid.uuid4().hex}',
                        company=location.company,
                        division=location.division,
                        location=location,
                        status=Asset.AssetStatus.AVAILABLE,
                        purchase_price=item.unit_price,
                        purchase_date=receipt.receipt_date,
                        source_quotation=purchase_order.quotation,
                        created_by=request.user if request.user.is_authenticated else None,
                    )
                    asset.save()
                    created_assets += 1

                item.quantity_received += qty
                item.save(update_fields=['quantity_received'])

            purchase_order.recalculate_progress()

            if purchase_order.status == PurchaseOrder.Status.COMPLETE:
                receipt.status = PurchaseReceipt.Status.COMPLETE
            else:
                receipt.status = PurchaseReceipt.Status.PARTIAL
            receipt.save(update_fields=['status'])

        messages.success(
            request,
            f'Received {created_assets} asset(s) for {purchase_order.po_number}.',
        )
        return redirect('dashboard:workflow_dashboard')

    return render(request, 'purchases/receipt.html', {
        'purchase_order': purchase_order,
        'items': items,
        'locations': available_locations,
    })
