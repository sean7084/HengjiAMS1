"""
URL configuration for Purchases app.
"""
from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseListView.as_view(), name='list'),
    path('stock/', views.StockOverviewView.as_view(), name='stock'),
    path('orders/<int:pk>/receive/', views.purchase_receipt_view, name='receive'),
    path('<uuid:pk>/', views.PurchaseDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit-serial/', views.edit_asset_serial, name='edit_serial'),
]
