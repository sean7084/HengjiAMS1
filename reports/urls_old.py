"""
URL configuration for reports app.
Handles reporting, analytics, and scheduled report URLs.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report Templates
    path('', views.ReportListView.as_view(), name='report_list'),
    path('templates/', views.ReportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/', views.ReportTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.ReportTemplateEditView.as_view(), name='template_edit'),
    
    # Report Generation
    path('generate/', views.ReportGenerateView.as_view(), name='report_generate'),
    path('generate/<uuid:template_pk>/', views.ReportGenerateFromTemplateView.as_view(), name='report_generate_from_template'),
    
    # Generated Reports
    path('generated/', views.GeneratedReportListView.as_view(), name='generated_report_list'),
    path('generated/<uuid:pk>/', views.GeneratedReportDetailView.as_view(), name='generated_report_detail'),
    path('generated/<uuid:pk>/download/', views.GeneratedReportDownloadView.as_view(), name='generated_report_download'),
    path('generated/<uuid:pk>/share/', views.GeneratedReportShareView.as_view(), name='generated_report_share'),
    path('generated/<uuid:pk>/delete/', views.GeneratedReportDeleteView.as_view(), name='generated_report_delete'),
    
    # Report Scheduling
    path('schedules/', views.ReportScheduleListView.as_view(), name='schedule_list'),
    path('schedules/create/', views.ReportScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<uuid:pk>/', views.ReportScheduleDetailView.as_view(), name='schedule_detail'),
    path('schedules/<uuid:pk>/edit/', views.ReportScheduleEditView.as_view(), name='schedule_edit'),
    path('schedules/<uuid:pk>/toggle/', views.ReportScheduleToggleView.as_view(), name='schedule_toggle'),
    path('schedules/<uuid:pk>/run-now/', views.ReportScheduleRunNowView.as_view(), name='schedule_run_now'),
    
    # Analytics and Dashboards
    path('analytics/', views.ReportAnalyticsView.as_view(), name='analytics'),
    path('dashboard/', views.ReportDashboardView.as_view(), name='dashboard'),
    
    # Pre-built Reports
    path('inventory/', views.InventoryReportView.as_view(), name='inventory_report'),
    path('valuation/', views.ValuationReportView.as_view(), name='valuation_report'),
    path('assignment-history/', views.AssignmentHistoryReportView.as_view(), name='assignment_history_report'),
    path('audit-summary/', views.AuditSummaryReportView.as_view(), name='audit_summary_report'),
    path('depreciation/', views.DepreciationReportView.as_view(), name='depreciation_report'),
    path('warranty-expiry/', views.WarrantyExpiryReportView.as_view(), name='warranty_expiry_report'),
    path('utilization/', views.UtilizationReportView.as_view(), name='utilization_report'),
    path('cost-analysis/', views.CostAnalysisReportView.as_view(), name='cost_analysis_report'),
    
    # Report Sharing
    path('shared/', views.SharedReportListView.as_view(), name='shared_report_list'),
    path('shares/<uuid:pk>/', views.ReportShareDetailView.as_view(), name='report_share_detail'),
    
    # API endpoints
    path('api/generate/', views.ReportGenerateAPIView.as_view(), name='report_generate_api'),
    path('api/status/<uuid:pk>/', views.ReportStatusAPIView.as_view(), name='report_status_api'),
]
