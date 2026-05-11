"""URL routes for deliveries app."""

from django.urls import path

from . import views

app_name = 'deliveries'

urlpatterns = [
    path('', views.DeliveryOrderListView.as_view(), name='list'),
    path('create/from-quotation/<int:quotation_pk>/', views.delivery_create_view, name='create_from_quotation'),
    path('<int:pk>/', views.DeliveryOrderDetailView.as_view(), name='detail'),
    path('<int:pk>/dispatch/', views.mark_dispatched, name='dispatch'),
    path('<int:pk>/upload-signed/', views.upload_signed_copy, name='upload_signed'),
    path('<int:pk>/complete/', views.mark_completed, name='complete'),
    path('<int:pk>/pdf/', views.generate_delivery_pdf, name='pdf'),
]
