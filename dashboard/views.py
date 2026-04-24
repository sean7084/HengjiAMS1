"""
Dashboard views for HengJi Asset Management System.
Provides main dashboard and overview functionality.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse
from assets.models import Asset, AssetCategory, AssetBrand, AssetMaintenance
from companies.models import Company, Division
from accounts.models import User
from deliveries.models import DeliveryOrder
from invoices.models import InvoiceInfo, WorkflowStatusAudit
from purchases.models import PurchaseOrder
from quotations.models import Quotation
import json


def _ensure_order_management_access(request):
    if request.user.can_manage_orders():
        return None
    messages.error(request, _('You do not have access to Order Management.'))
    return redirect('dashboard:dashboard')


@login_required
def dashboard_view(request):
    """
    Main dashboard view showing system overview and key metrics.
    """
    user = request.user

    # Get accessible assets based on user's admin role
    accessible_assets = user.get_accessible_assets()

    # Asset statistics
    total_assets = accessible_assets.count()
    assets_by_status = accessible_assets.values('status').annotate(count=Count('id'))
    assets_by_category = accessible_assets.values('category__name').annotate(count=Count('id'))[:5]
    pending_maintenance = AssetMaintenance.objects.filter(
        asset__in=accessible_assets,
        status='scheduled'
    ).count()
    recent_assets = accessible_assets.order_by('-created_at')[:5]

    # Get user's company context for display
    user_company = user.company if hasattr(user, 'company') and user.company else None

    # Convert status QuerySet to dictionary for easier template access
    status_stats = {item['status']: item['count'] for item in assets_by_status}

    # System statistics
    total_companies = Company.objects.count()
    total_users = User.objects.count()
    total_categories = AssetCategory.objects.count()
    total_brands = AssetBrand.objects.count()

    # Recent activity (placeholder for now)
    recent_activities = []

    # Get dashboard preferences from session
    dashboard_config = request.session.get('dashboard_config', {})

    context = {
        'user_company': user_company,
        'total_assets': total_assets,
        'total_companies': total_companies,
        'total_users': total_users,
        'total_categories': total_categories,
        'total_brands': total_brands,
        'pending_maintenance': pending_maintenance,
        'status_stats': status_stats,
        'assets_by_category': assets_by_category,
        'recent_assets': recent_assets,
        'recent_activities': recent_activities,
        'available_assets': status_stats.get('available', 0),
        'assigned_assets': status_stats.get('assigned', 0),
        'maintenance_assets': status_stats.get('maintenance', 0),
        'retired_assets': status_stats.get('retired', 0),
        'dashboard_config': json.dumps(dashboard_config),
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def quick_stats_view(request):
    """
    API-like view for quick stats (for AJAX updates).
    """
    user = request.user
    accessible_assets = user.get_accessible_assets()

    stats = {
        'total_assets': accessible_assets.count(),
        'available_assets': accessible_assets.filter(status='available').count(),
        'assigned_assets': accessible_assets.filter(status='assigned').count(),
        'maintenance_assets': accessible_assets.filter(status='maintenance').count(),
    }

    return render(request, 'dashboard/quick_stats.html', {'stats': stats})


@login_required
def save_dashboard_config(request):
    """
    Save dashboard configuration to session.
    """
    if request.method == 'POST':
        config = json.loads(request.body or '{}')
        request.session['dashboard_config'] = config
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def workflow_dashboard_view(request):
    """Q9 integrated workflow dashboard with kanban stages and status audit stream."""
    denied_response = _ensure_order_management_access(request)
    if denied_response:
        return denied_response
    quotation_stage_qs = Quotation.objects.filter(status__in=['draft', 'sent']).select_related('customer').order_by('-created_at')
    confirmed_stage_qs = Quotation.objects.filter(status='confirmed').select_related('customer').order_by('-created_at')
    purchased_stage_qs = PurchaseOrder.objects.select_related('quotation', 'quotation__customer').order_by('-created_at')
    dispatched_stage_qs = DeliveryOrder.objects.filter(status='dispatched').select_related('quotation', 'quotation__customer').order_by('-created_at')
    delivered_stage_qs = DeliveryOrder.objects.filter(status='completed').select_related('quotation', 'quotation__customer').order_by('-created_at')
    invoiced_stage_qs = InvoiceInfo.objects.select_related('quotation', 'delivery_order').order_by('-created_at')

    workflow_stages = [
        {
            'key': 'quotation',
            'title': 'Quotations',
            'count': quotation_stage_qs.count(),
            'value': quotation_stage_qs.aggregate(total=Sum('total_with_tax')).get('total') or 0,
            'items': quotation_stage_qs[:8],
        },
        {
            'key': 'confirmed',
            'title': 'Confirmed',
            'count': confirmed_stage_qs.count(),
            'value': confirmed_stage_qs.aggregate(total=Sum('total_with_tax')).get('total') or 0,
            'items': confirmed_stage_qs[:8],
        },
        {
            'key': 'purchased',
            'title': 'Purchased',
            'count': purchased_stage_qs.count(),
            'value': purchased_stage_qs.aggregate(total=Sum('quotation__total_with_tax')).get('total') or 0,
            'items': purchased_stage_qs[:8],
        },
        {
            'key': 'dispatched',
            'title': 'Dispatched',
            'count': dispatched_stage_qs.count(),
            'value': dispatched_stage_qs.aggregate(total=Sum('quotation__total_with_tax')).get('total') or 0,
            'items': dispatched_stage_qs[:8],
        },
        {
            'key': 'delivered',
            'title': 'Delivered',
            'count': delivered_stage_qs.count(),
            'value': delivered_stage_qs.aggregate(total=Sum('quotation__total_with_tax')).get('total') or 0,
            'items': delivered_stage_qs[:8],
        },
        {
            'key': 'invoiced',
            'title': 'Invoiced',
            'count': invoiced_stage_qs.count(),
            'value': invoiced_stage_qs.aggregate(total=Sum('gross_amount')).get('total') or 0,
            'items': invoiced_stage_qs[:8],
        },
    ]

    recent_status_audits = WorkflowStatusAudit.objects.order_by('-changed_at')[:40]

    context = {
        'workflow_stages': workflow_stages,
        'recent_status_audits': recent_status_audits,
    }
    return render(request, 'dashboard/workflow_dashboard.html', context)


@login_required
def workflow_search_view(request):
    """Q9 cross-search across quotations, deliveries, and invoices."""
    denied_response = _ensure_order_management_access(request)
    if denied_response:
        return denied_response
    query = (request.GET.get('q') or '').strip()

    quotation_results = Quotation.objects.none()
    delivery_results = DeliveryOrder.objects.none()
    invoice_results = InvoiceInfo.objects.none()

    if query:
        quotation_results = Quotation.objects.select_related('customer').filter(
            Q(quotation_number__icontains=query)
            | Q(customer__name__icontains=query)
            | Q(attn__icontains=query)
            | Q(tel__icontains=query)
        ).order_by('-created_at')[:30]

        delivery_results = DeliveryOrder.objects.select_related('quotation', 'quotation__customer').filter(
            Q(delivery_number__icontains=query)
            | Q(quotation__quotation_number__icontains=query)
            | Q(quotation__customer__name__icontains=query)
            | Q(receiver_name__icontains=query)
            | Q(receiver_phone__icontains=query)
        ).order_by('-created_at')[:30]

        invoice_results = InvoiceInfo.objects.select_related('quotation', 'delivery_order').filter(
            Q(invoice_number__icontains=query)
            | Q(bill_to__icontains=query)
            | Q(kering_group_po_number__icontains=query)
            | Q(internal_order__icontains=query)
            | Q(sap_cost_center__icontains=query)
            | Q(quotation__quotation_number__icontains=query)
            | Q(delivery_order__delivery_number__icontains=query)
        ).order_by('-created_at')[:30]

    context = {
        'query': query,
        'quotation_results': quotation_results,
        'delivery_results': delivery_results,
        'invoice_results': invoice_results,
        'result_count': quotation_results.count() + delivery_results.count() + invoice_results.count(),
    }

    return render(request, 'dashboard/workflow_search.html', context)
