"""
URL configuration for Products app.
"""
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductPriceListView.as_view(), name='price_list'),
    path('add/', views.ProductPriceCreateView.as_view(), name='price_add'),
    path('<int:pk>/edit/', views.ProductPriceUpdateView.as_view(), name='price_edit'),
    path('<int:pk>/delete/', views.ProductPriceDeleteView.as_view(), name='price_delete'),
    path('import/', views.import_prices_view, name='price_import'),
    path('import/template/', views.download_import_template, name='price_import_template'),
]
