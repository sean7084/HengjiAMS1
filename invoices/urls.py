from django.urls import path

from . import views

app_name = 'invoices'

urlpatterns = [
    path('', views.WeeklyOrderBatchListView.as_view(), name='batch_list'),
    path('import/', views.import_sharepoint_batch_view, name='batch_import'),
    path('<int:pk>/', views.WeeklyOrderBatchDetailView.as_view(), name='batch_detail'),
    path('invoice-info/', views.InvoiceInfoListView.as_view(), name='invoice_list'),
    path('invoice-info/export/', views.invoice_info_export_view, name='invoice_export'),
    path('invoice-info/<int:pk>/', views.InvoiceInfoDetailView.as_view(), name='invoice_detail'),
    path('invoice-info/<int:pk>/update/', views.invoice_info_update_view, name='invoice_update'),
    path('invoice-info/<int:pk>/recalculate/', views.invoice_info_recalculate_view, name='invoice_recalculate'),
    path('invoice-info/<int:pk>/document/', views.invoice_info_document_view, name='invoice_document'),
    path('emails/', views.EmailDispatchListView.as_view(), name='email_dispatch_list'),
    path('emails/compose/', views.email_dispatch_compose_view, name='email_dispatch_compose'),
    path('emails/compose/quotation/<int:quotation_pk>/', views.email_dispatch_compose_view, name='email_dispatch_compose_from_quotation'),
    path('emails/<int:pk>/client-confirmed/', views.email_dispatch_mark_client_confirmed_view, name='email_dispatch_client_confirmed'),
    path('emails/<int:pk>/esker-forward/', views.email_dispatch_mark_esker_view, name='email_dispatch_esker_forward'),
]
