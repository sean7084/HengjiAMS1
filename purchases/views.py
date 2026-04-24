"""
Views for Purchases app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone
import uuid

from assets.models import Asset
from quotations.models import Quotation
from .models import PurchaseOrder, PurchaseOrderItem, PurchaseReceipt


class OrderManagementAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_orders()

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')


class PurchaseListView(OrderManagementAccessMixin, ListView):
    """List view for purchased assets from quotations."""
    model = Asset
    template_name = 'purchases/list.html'
    context_object_name = 'assets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Asset.objects.filter(
            source_quotation__isnull=False
        ).select_related('source_quotation', 'brand', 'model', 'category')

        # Filter by quotation
        quotation_id = self.request.GET.get('quotation')
        if quotation_id:
            queryset = queryset.filter(source_quotation_id=quotation_id)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_number__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Asset.AssetStatus.choices
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_quotation'] = self.request.GET.get('quotation', '')
        context['quotations'] = Quotation.objects.filter(
            purchased_assets__isnull=False
        ).distinct().order_by('-created_at')
        return context


class StockOverviewView(OrderManagementAccessMixin, ListView):
    """Overview of stock from purchased assets."""
    model = Asset
    template_name = 'purchases/stock.html'
    context_object_name = 'assets'

    def get_queryset(self):
        return Asset.objects.filter(
            source_quotation__isnull=False
        ).select_related('source_quotation', 'brand', 'model', 'category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assets = self.get_queryset()
        purchase_orders = PurchaseOrder.objects.select_related('quotation')

        # Summary stats
        context['total_count'] = assets.count()
        context['available_count'] = assets.filter(status='available').count()
        context['assigned_count'] = assets.filter(status='assigned').count()
        context['in_use_count'] = assets.filter(status='in_use').count()
        context['po_total'] = purchase_orders.count()
        context['po_receiving'] = purchase_orders.filter(status=PurchaseOrder.Status.RECEIVING).count()
        context['po_complete'] = purchase_orders.filter(status=PurchaseOrder.Status.COMPLETE).count()
        context['converted_quotations'] = Quotation.objects.filter(purchase_order__isnull=False).count()

        # Ready for dispatch = purchased assets currently available.
        context['ready_dispatch_count'] = assets.filter(status=Asset.AssetStatus.AVAILABLE).count()

        # Group by brand
        context['by_brand'] = {}
        for asset in assets:
            brand_name = asset.brand.name if asset.brand else 'Unknown'
            if brand_name not in context['by_brand']:
                context['by_brand'][brand_name] = {
                    'total': 0,
                    'available': 0,
                    'assigned': 0,
                }
            context['by_brand'][brand_name]['total'] += 1
            if asset.status == 'available':
                context['by_brand'][brand_name]['available'] += 1
            elif asset.status == 'assigned':
                context['by_brand'][brand_name]['assigned'] += 1

        # Group by source quotation
        context['by_quotation'] = {}
        for asset in assets:
            qn = asset.source_quotation.quotation_number if asset.source_quotation else 'Unknown'
            if qn not in context['by_quotation']:
                context['by_quotation'][qn] = {
                    'total': 0,
                    'available': 0,
                    'assets': [],
                    'quotation_pk': asset.source_quotation.pk if asset.source_quotation else None,
                }
            context['by_quotation'][qn]['total'] += 1
            context['by_quotation'][qn]['assets'].append(asset)
            if asset.status == 'available':
                context['by_quotation'][qn]['available'] += 1

        context['by_location'] = assets.values(
            'location__name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')

        context['recent_receipts'] = PurchaseReceipt.objects.select_related(
            'purchase_order', 'quotation', 'location'
        ).order_by('-created_at')[:10]

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

    available_locations = purchase_order.quotation.customer.locations.filter(status='active').order_by('name')

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
        return redirect('purchases:stock')

    return render(request, 'purchases/receipt.html', {
        'purchase_order': purchase_order,
        'items': items,
        'locations': available_locations,
    })
