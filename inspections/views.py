"""
Web views for the inspections module.

Complements the mini-program REST API (``api/inspection_views.py``) with a
server-rendered UI for planning, browsing, and exporting store inspections.

Access model:
- ``can_view_inspections()`` (superadmin / IT admin / inspection engineer) gates
  every view in this module.
- ``can_manage_inspections()`` (superadmin / IT admin) gates batch creation,
  schedule import, and batch editing.
- Engineers see only their own inspections via ``user.get_assigned_inspections()``.
"""
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView, DetailView, ListView, TemplateView, UpdateView,
)

from companies.models import Location
from inspections.forms import (
    AssetListExportForm,
    InspectionBatchByBrandForm,
    ScheduleImportForm,
    StoreInspectionFilterForm,
)
from inspections.models import InspectionBatch, InspectionDevice, StoreInspection
from inspections.services.asset_list_export import export_asset_list
from inspections.services.kering_import import import_kering_master

# FullCalendar event colors keyed by StoreInspection.Status.
_STATUS_COLORS = {
    StoreInspection.Status.PLANNED: '#6c757d',
    StoreInspection.Status.IN_PROGRESS: '#0dcaf0',
    StoreInspection.Status.COMPLETED: '#198754',
    StoreInspection.Status.SUBMITTED: '#6610f2',
}


# -- mixins ------------------------------------------------------------------
class InspectionAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require an authenticated user with inspections-module read access."""

    def test_func(self):
        return self.request.user.can_view_inspections()


class InspectionManageMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Require an authenticated user with inspections-module write access."""

    def test_func(self):
        return self.request.user.can_manage_inspections()


def _scoped_inspections(user):
    """Return the StoreInspection queryset the given user may see."""
    return user.get_assigned_inspections().select_related(
        'batch', 'company', 'division', 'location', 'engineer'
    )


# -- dashboard ---------------------------------------------------------------
class InspectionDashboardView(InspectionAccessMixin, TemplateView):
    """Monthly FullCalendar view of the user's inspections."""

    template_name = 'inspections/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        inspections = _scoped_inspections(user)

        # Optional batch filter (query string) so the dashboard can be scoped
        # to one planning cycle from the batch detail page.
        batch_id = self.request.GET.get('batch')
        batch = None
        if batch_id:
            batch = InspectionBatch.objects.filter(id=batch_id).first()
            if batch:
                inspections = inspections.filter(batch=batch)

        # Build FullCalendar event payloads.
        events = []
        for inspection in inspections:
            events.append({
                'id': str(inspection.id),
                'title': inspection.store_label or str(inspection),
                'start': inspection.inspection_date.isoformat() if inspection.inspection_date else None,
                'url': reverse('inspections:inspection_detail', args=[inspection.id]),
                'backgroundColor': _STATUS_COLORS.get(inspection.status, '#6c757d'),
                'borderColor': _STATUS_COLORS.get(inspection.status, '#6c757d'),
                'extendedProps': {
                    'brand': inspection.brand_name or (inspection.division.name if inspection.division else ''),
                    'engineer': inspection.engineer.get_full_name() if inspection.engineer else '',
                    'status': inspection.get_status_display(),
                    'jda': inspection.jda_code,
                },
            })

        # Summary tiles for the current month (or the batch's date range).
        today = timezone.localdate()
        if batch:
            month_start = batch.start_date
            month_end = batch.end_date
        else:
            month_start = today.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        in_range = inspections.filter(
            inspection_date__gte=month_start, inspection_date__lte=month_end
        )
        context.update({
            'events_json': json.dumps(events),
            'batch': batch,
            'batches': InspectionBatch.objects.filter(
                company__in=user.get_accessible_companies()
            ).order_by('-start_date')[:50],
            'month_start': month_start,
            'month_end': month_end,
            'total_count': in_range.count(),
            'planned_count': in_range.filter(status=StoreInspection.Status.PLANNED).count(),
            'in_progress_count': in_range.filter(status=StoreInspection.Status.IN_PROGRESS).count(),
            'completed_count': in_range.filter(status=StoreInspection.Status.COMPLETED).count(),
            'submitted_count': in_range.filter(status=StoreInspection.Status.SUBMITTED).count(),
            'can_manage': user.can_manage_inspections(),
        })
        return context


# -- batch list / create / detail / update -----------------------------------
class InspectionBatchListView(InspectionAccessMixin, ListView):
    model = InspectionBatch
    template_name = 'inspections/batch_list.html'
    context_object_name = 'batches'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = InspectionBatch.objects.filter(
            company__in=user.get_accessible_companies()
        ).select_related('company', 'division', 'engineer').annotate(
            inspection_count=Count('inspections')
        )
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(division__name__icontains=search)
            )
        source = self.request.GET.get('source', '').strip()
        if source:
            qs = qs.filter(source=source)
        return qs.order_by('-start_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['source'] = self.request.GET.get('source', '')
        context['source_choices'] = InspectionBatch.Source.choices
        context['can_manage'] = self.request.user.can_manage_inspections()
        return context


class InspectionBatchCreateView(InspectionManageMixin, TemplateView):
    """Landing page: choose between by-brand and schedule-upload flows."""

    template_name = 'inspections/batch_create.html'


class InspectionBatchCreateByBrandView(InspectionManageMixin, CreateView):
    """Create a batch + auto-spread one inspection per active store location."""

    model = InspectionBatch
    form_class = InspectionBatchByBrandForm
    template_name = 'inspections/batch_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Batch by Brand')
        context['submit_text'] = _('Create Batch & Schedule Stores')
        context['back_url'] = reverse('inspections:batch_create')
        context['mode'] = 'by-brand'
        return context

    def form_valid(self, form):
        user = self.request.user
        with transaction.atomic():
            batch = form.save(commit=False)
            batch.source = InspectionBatch.Source.BRAND
            batch.created_by = user
            batch.save()
            form.save_m2m()

            created = self._spread_stores(batch, user)

        messages.success(
            self.request,
            _('Batch "%(name)s" created with %(count)s store inspections.') % {
                'name': batch.name, 'count': created,
            }
        )
        return redirect('inspections:batch_detail', pk=batch.pk)

    def _spread_stores(self, batch, user):
        """Round-robin the division's active store locations across the date range."""
        locations = Location.objects.filter(
            division=batch.division,
            location_type=Location.LocationType.STORE,
            status=Location.LocationStatus.ACTIVE,
        ).order_by('code', 'name')

        total_days = (batch.end_date - batch.start_date).days + 1
        if total_days <= 0:
            total_days = 1
        dates = [batch.start_date + timedelta(days=i) for i in range(total_days)]

        created = 0
        for index, location in enumerate(locations):
            inspection_date = dates[index % len(dates)]
            store_label = ' '.join(
                part for part in [location.code, batch.division.name, location.name] if part
            ).strip()
            _inspection, was_created = StoreInspection.objects.get_or_create(
                location=location,
                inspection_date=inspection_date,
                defaults={
                    'batch': batch,
                    'company': batch.company,
                    'division': batch.division,
                    'engineer': batch.engineer,
                    'jda_code': location.code or '',
                    'brand_name': batch.division.name if batch.division else '',
                    'store_name': location.name,
                    'store_label': store_label,
                    'status': StoreInspection.Status.PLANNED,
                    'created_by': user,
                },
            )
            if was_created:
                created += 1
        return created


class InspectionBatchImportView(InspectionManageMixin, View):
    """Upload schedule.xlsx (+ optional asset_list.xlsx) to create a batch."""

    template_name = 'inspections/batch_import.html'

    def get(self, request):
        form = ScheduleImportForm(user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'title': _('Import Schedule'),
            'back_url': reverse('inspections:batch_create'),
        })

    def post(self, request):
        form = ScheduleImportForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'title': _('Import Schedule'),
                'back_url': reverse('inspections:batch_create'),
            })

        company = form.cleaned_data['company']
        name = form.cleaned_data['name']
        schedule_file = form.cleaned_data['schedule_file']
        assets_file = form.cleaned_data.get('assets_file')
        engineer = form.cleaned_data.get('engineer')
        description = form.cleaned_data.get('description', '')

        # Derive a provisional date range from the schedule contents so the batch
        # record has sensible start/end dates even before the import runs.
        # The importer will create the inspections; we just need a placeholder
        # range that the user can edit later.
        today = timezone.localdate()
        batch = InspectionBatch.objects.create(
            name=name,
            company=company,
            division=None,
            engineer=engineer,
            start_date=today,
            end_date=today + timedelta(days=30),
            description=description,
            source=InspectionBatch.Source.UPLOAD,
            created_by=request.user,
        )

        try:
            result = import_kering_master(
                schedule_file,
                assets_file,
                company_name=company.name,
                company_code=company.code,
                engineer=engineer,
                batch=batch,
                user=request.user,
                dry_run=False,
                track_rollback=True,
            )
        except Exception as exc:  # pragma: no cover - surfaced to the user
            batch.delete()
            messages.error(self.request, _('Import failed: %(error)s') % {'error': exc})
            return render(request, self.template_name, {
                'form': form,
                'title': _('Import Schedule'),
                'back_url': reverse('inspections:batch_create'),
            })

        stats = result['stats']
        per_store = result['per_store']

        # Tighten the batch date range to match what was actually imported.
        imported_inspections = StoreInspection.objects.filter(batch=batch)
        if imported_inspections.exists():
            min_date = imported_inspections.order_by('inspection_date').first().inspection_date
            max_date = imported_inspections.order_by('-inspection_date').first().inspection_date
            # Infer the division from the first inspection with one (schedule may
            # mix brands; pick the most common).
            division = (
                imported_inspections.exclude(division__isnull=True)
                .values('division').annotate(n=Count('id')).order_by('-n').first()
            )
            batch.start_date = min_date or batch.start_date
            batch.end_date = max_date or batch.end_date
            if division:
                from companies.models import Division
                batch.division = Division.objects.filter(id=division['division']).first()
            batch.save(update_fields=['start_date', 'end_date', 'division', 'updated_at'])

        messages.success(
            self.request,
            _('Imported %(inspections)s inspections, %(devices)s expected devices, '
              '%(assets)s assets across %(stores)s stores.') % {
                'inspections': stats['inspections'],
                'devices': stats['devices'],
                'assets': stats['assets'],
                'stores': len(per_store),
            }
        )
        return redirect('inspections:batch_detail', pk=batch.pk)


class InspectionBatchDetailView(InspectionAccessMixin, DetailView):
    model = InspectionBatch
    template_name = 'inspections/batch_detail.html'
    context_object_name = 'batch'

    def get_queryset(self):
        return InspectionBatch.objects.filter(
            company__in=self.request.user.get_accessible_companies()
        ).select_related('company', 'division', 'engineer', 'import_run', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object
        inspections = (
            StoreInspection.objects.filter(batch=batch)
            .select_related('location', 'division', 'engineer')
            .annotate(device_total=Count('devices'))
            .order_by('inspection_date', 'jda_code')
        )
        # Per-inspection collected count for the progress column.
        collected_map = dict(
            InspectionDevice.objects
            .filter(store_inspection__batch=batch, collected_at__isnull=False)
            .values('store_inspection_id')
            .annotate(n=Count('id'))
            .values_list('store_inspection_id', 'n')
        )
        rows = []
        for inspection in inspections:
            collected = collected_map.get(inspection.id, 0)
            total = inspection.device_total or 0
            pct = round((collected / total) * 100, 1) if total else 0
            rows.append({
                'inspection': inspection,
                'collected': collected,
                'total': total,
                'pct': pct,
            })
        context.update({
            'rows': rows,
            'inspection_count': len(rows),
            'completion_pct': batch.get_completion_percentage(),
            'can_manage': self.request.user.can_manage_inspections(),
            'export_url': f'{reverse("inspections:asset_list_export")}?batch={batch.id}',
        })
        return context


class InspectionBatchUpdateView(InspectionManageMixin, UpdateView):
    model = InspectionBatch
    form_class = InspectionBatchByBrandForm
    template_name = 'inspections/batch_form.html'

    def get_queryset(self):
        return InspectionBatch.objects.filter(
            company__in=self.request.user.get_accessible_companies()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('inspections:batch_detail', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Batch')
        context['submit_text'] = _('Save Changes')
        context['back_url'] = reverse('inspections:batch_detail', args=[self.object.pk])
        context['mode'] = 'edit'
        return context


# -- inspection list / detail ------------------------------------------------
class StoreInspectionListView(InspectionAccessMixin, ListView):
    model = StoreInspection
    template_name = 'inspections/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 30

    def get_queryset(self):
        qs = _scoped_inspections(self.request.user)
        form = StoreInspectionFilterForm(self.request.GET, user=self.request.user)
        self.filter_form = form
        if form.is_valid():
            data = form.cleaned_data
            if data.get('batch'):
                qs = qs.filter(batch=data['batch'])
            if data.get('division'):
                qs = qs.filter(division=data['division'])
            if data.get('status'):
                qs = qs.filter(status=data['status'])
            if data.get('engineer'):
                qs = qs.filter(engineer=data['engineer'])
            if data.get('date_from'):
                qs = qs.filter(inspection_date__gte=data['date_from'])
            if data.get('date_to'):
                qs = qs.filter(inspection_date__lte=data['date_to'])
            if data.get('search'):
                needle = data['search']
                qs = qs.filter(
                    Q(store_label__icontains=needle)
                    | Q(jda_code__icontains=needle)
                    | Q(store_name__icontains=needle)
                    | Q(brand_name__icontains=needle)
                )
        return qs.order_by('-inspection_date', 'jda_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['can_manage'] = self.request.user.can_manage_inspections()
        return context


class StoreInspectionDetailView(InspectionAccessMixin, DetailView):
    model = StoreInspection
    template_name = 'inspections/inspection_detail.html'
    context_object_name = 'inspection'

    def get_queryset(self):
        return _scoped_inspections(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inspection = self.object
        devices = (
            inspection.devices.select_related('asset', 'collected_by')
            .prefetch_related('photos').order_by('row_order', 'created_at')
        )
        issues = inspection.issues.all().order_by('seq', 'created_at')
        photos = inspection.photos.filter(device__isnull=True).order_by('kind', 'sort_index')
        context.update({
            'devices': devices,
            'issues': issues,
            'store_photos': photos,
            'device_total': devices.count(),
            'device_collected': devices.filter(collected_at__isnull=False).count(),
            'completion_pct': inspection.get_completion_percentage(),
            'can_manage': self.request.user.can_manage_inspections(),
        })
        return context


# -- asset list export -------------------------------------------------------
class AssetListExportView(InspectionAccessMixin, View):
    """GET renders the filter form; POST streams the xlsx download."""

    template_name = 'inspections/export_form.html'

    def get(self, request):
        form = AssetListExportForm(request.GET or None, user=request.user)
        # Pre-fill batch from ?batch=<id> so the batch-detail "Export" button
        # lands here with the batch already selected.
        batch_id = request.GET.get('batch')
        if batch_id and not form.is_bound:
            batch = InspectionBatch.objects.filter(id=batch_id).first()
            if batch:
                form = AssetListExportForm(initial={'batch': batch}, user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'title': _('Export Asset List'),
        })

    def post(self, request):
        form = AssetListExportForm(request.POST, user=request.user)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'title': _('Export Asset List'),
            })

        inspections = list(form.resolve_inspections())
        if not inspections:
            messages.warning(request, _('No inspections match the selected filters.'))
            return render(request, self.template_name, {
                'form': form,
                'title': _('Export Asset List'),
            })

        batch = form.cleaned_data.get('batch')
        content, filename = export_asset_list(inspections, batch=batch)

        response = HttpResponse(
            content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
