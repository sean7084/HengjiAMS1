"""Views for delivery order workflow."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView

from assets.models import Asset
from customers.models import CustomerProfile
from quotations.models import Quotation

from .forms import DeliveryOrderForm, SignedCopyUploadForm
from .models import DeliveryItem, DeliveryOrder
from .services import convert_xlsx_to_pdf, fill_delivery_template


class DeliveryOrderListView(ListView):
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


class DeliveryOrderDetailView(DetailView):
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

    quotation = get_object_or_404(
        Quotation.objects.select_related('customer', 'customer_profile'),
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
    }

    if quotation.customer_profile_id:
        profile = quotation.customer_profile
    else:
        profile = CustomerProfile.objects.filter(company=quotation.customer).first()

    if profile:
        initial_data.update({
            'receiver_name': profile.delivery_contact,
            'receiver_phone': profile.delivery_phone,
            'delivery_address': f'{profile.delivery_address} {profile.delivery_city}'.strip(),
            'delivery_method': profile.get_delivery_method_display(),
        })

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
    """Generate delivery document from template and return PDF (or xlsx fallback)."""

    delivery = get_object_or_404(DeliveryOrder.objects.prefetch_related('items'), pk=pk)

    try:
        xlsx_path = fill_delivery_template(delivery)
    except FileNotFoundError as exc:
        messages.error(request, str(exc))
        return redirect('deliveries:detail', pk=pk)

    pdf_path = convert_xlsx_to_pdf(xlsx_path)

    if pdf_path:
        return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=pdf_path.name)

    messages.warning(
        request,
        'PDF converter not found. Downloading filled Excel file instead.',
    )
    return FileResponse(open(xlsx_path, 'rb'), as_attachment=True, filename=xlsx_path.name)
