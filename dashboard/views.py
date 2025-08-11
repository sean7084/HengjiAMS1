"""
Dashboard views for HengJi Asset Management System.
Provides main dashboard and overview functionality.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from assets.models import Asset, AssetCategory, AssetBrand, AssetMaintenance
from companies.models import Company, Division
from accounts.models import User


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
