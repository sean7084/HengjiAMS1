"""
Views for Companies app.
Provides company, division, location, and company user management.
"""
import csv
import io

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Company, Division, Location, CompanyUser, ImportRunChange
from .forms import CompanyForm, DivisionForm, LocationForm, CompanyUserForm, CSVImportForm
from accounts.models import User
from utils.csv_import import read_csv_rows_with_fallback, normalize_headers_and_rows
from utils.import_rollback import (
    snapshot_instance,
    start_import_run,
    finalize_import_run,
    record_import_change,
    get_latest_rollback_run,
    rollback_run,
)


class CompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing companies.
    """
    model = Company
    template_name = 'companies/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Company.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Company Management')
        context['search'] = self.request.GET.get('search', '')
        context['import_url'] = reverse('companies:company_import_csv')
        return context


class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new companies.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Company created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Company')
        context['action'] = _('Create')
        return context


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating companies.
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Company updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Company')
        context['action'] = _('Update')
        return context


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting companies.
    """
    model = Company
    template_name = 'companies/company_confirm_delete.html'
    success_url = reverse_lazy('companies:company_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Company deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Company')
        return context


class DivisionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing divisions.
    """
    model = Division
    template_name = 'companies/division_list.html'
    context_object_name = 'divisions'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Division.objects.select_related('company').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(company__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Division Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class DivisionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new divisions.
    """
    model = Division
    form_class = DivisionForm
    template_name = 'companies/division_form.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Division created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Division')
        context['action'] = _('Create')
        return context


class DivisionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating divisions.
    """
    model = Division
    form_class = DivisionForm
    template_name = 'companies/division_form.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Division updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Division')
        context['action'] = _('Update')
        return context


class DivisionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting divisions.
    """
    model = Division
    template_name = 'companies/division_confirm_delete.html'
    success_url = reverse_lazy('companies:division_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Division deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Division')
        return context


class LocationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing locations.
    """
    model = Location
    template_name = 'companies/location_list.html'
    context_object_name = 'locations'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = Location.objects.select_related('company', 'manager').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(address_line1__icontains=search) |
                Q(address_line2__icontains=search) |
                Q(city__icontains=search) |
                Q(code__icontains=search) |
                Q(zone__icontains=search) |
                Q(rack__icontains=search) |
                Q(shelf__icontains=search) |
                Q(company__name__icontains=search) |
                Q(manager__first_name__icontains=search) |
                Q(manager__last_name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Location Management')
        context['search'] = self.request.GET.get('search', '')
        context['import_url'] = reverse('companies:location_import_csv')

        paginator = context.get('paginator')
        if paginator is not None:
            context['total_location_count'] = paginator.count
        else:
            context['total_location_count'] = len(context.get('locations') or [])

        all_locations = context.get('locations')
        if all_locations is not None:
            warehouses = [location for location in all_locations if location.location_type == Location.LocationType.WAREHOUSE]
            context['warehouse_count'] = len(warehouses)
            context['slot_total'] = sum(location.get_slot_count() for location in warehouses)
        return context


class LocationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new locations.
    """
    model = Location
    form_class = LocationForm
    template_name = 'companies/location_form.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Location created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Location')
        context['action'] = _('Create')
        return context


class LocationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating locations.
    """
    model = Location
    form_class = LocationForm
    template_name = 'companies/location_form.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def form_valid(self, form):
        messages.success(self.request, _('Location updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Location')
        context['action'] = _('Update')
        return context


class LocationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting locations.
    """
    model = Location
    template_name = 'companies/location_confirm_delete.html'
    success_url = reverse_lazy('companies:location_list')
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Location deleted successfully.'))
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Location')
        return context


class CompanyUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing company users.
    """
    model = CompanyUser
    template_name = 'companies/companyuser_list.html'
    context_object_name = 'company_users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_manage_companies()
    
    def get_queryset(self):
        queryset = CompanyUser.objects.select_related('user', 'company', 'location').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(work_email__icontains=search) |
                Q(work_phone__icontains=search) |
                Q(company__name__icontains=search) |
                Q(location__name__icontains=search)
            )
        
        return queryset.order_by('company__name', 'name', 'user__username')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Company Contact Management')
        context['search'] = self.request.GET.get('search', '')
        context['import_url'] = reverse('companies:company_contact_import_csv')
        return context


class CompanyUserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating company contacts/recipient records."""
    model = CompanyUser
    form_class = CompanyUserForm
    template_name = 'companies/companyuser_form.html'
    success_url = reverse_lazy('companies:companyuser_list')

    def test_func(self):
        return self.request.user.can_manage_companies()

    def form_valid(self, form):
        messages.success(self.request, _('Company contact added successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Company Contact')
        context['action'] = _('Create')
        context['required_fields'] = [_('Name'), _('Company'), _('Role')]
        return context


class CompanyUserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for editing company contact records."""
    model = CompanyUser
    form_class = CompanyUserForm
    template_name = 'companies/companyuser_form.html'
    success_url = reverse_lazy('companies:companyuser_list')

    def test_func(self):
        return self.request.user.can_manage_companies()

    def form_valid(self, form):
        messages.success(self.request, _('Company contact updated successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Company Contact')
        context['action'] = _('Update')
        context['required_fields'] = [_('Name'), _('Company'), _('Role')]
        return context


def _normalize_csv_cell(value):
    return (value or '').strip()


def _normalize_csv_header(header):
    normalized_headers, _ = normalize_headers_and_rows([header], [])
    return normalized_headers[0] if normalized_headers else ''


def _normalize_csv_headers_and_rows(headers, rows):
    return normalize_headers_and_rows(headers, rows)


def _read_csv_rows_with_fallback(file_obj):
    try:
        return read_csv_rows_with_fallback(file_obj)
    except UnicodeDecodeError as exc:
        raise ValueError(
            _('Unable to decode CSV file. Please save it as UTF-8, GBK/GB18030, or Big5 and try again.')
        ) from exc


def _can_manage_companies(request):
    return request.user.is_authenticated and request.user.can_manage_companies()


IMPORT_PREVIEW_SESSION_KEY = 'companies_csv_import_preview'


def _store_import_preview(request, import_type, headers, rows):
    request.session[IMPORT_PREVIEW_SESSION_KEY] = {
        'import_type': import_type,
        'headers': headers,
        'rows': rows,
    }
    request.session.modified = True


def _get_import_preview(request, import_type):
    payload = request.session.get(IMPORT_PREVIEW_SESSION_KEY)
    if not payload:
        return None
    if payload.get('import_type') != import_type:
        return None
    return payload


def _clear_import_preview(request):
    if IMPORT_PREVIEW_SESSION_KEY in request.session:
        del request.session[IMPORT_PREVIEW_SESSION_KEY]
        request.session.modified = True


def _build_preview_matrix(headers, rows, limit=20):
    matrix = []
    for row in rows[:limit]:
        matrix.append([row.get(header, '') for header in headers])
    return matrix


COMPANIES_IMPORT_MODULE = 'companies'


def _companies_rollback_route_name(import_type):
    return {
        'company': 'companies:company_import_rollback',
        'location': 'companies:location_import_rollback',
        'company_contact': 'companies:company_contact_import_rollback',
    }.get(import_type)


def _companies_latest_rollback_url(request, import_type):
    route_name = _companies_rollback_route_name(import_type)
    if not route_name:
        return None

    latest_run = get_latest_rollback_run(request.user, COMPANIES_IMPORT_MODULE, import_type)
    if latest_run is None:
        return None
    return reverse(route_name)


def _perform_companies_rollback(request, import_type, redirect_route):
    run = get_latest_rollback_run(request.user, COMPANIES_IMPORT_MODULE, import_type)
    if run is None:
        messages.warning(request, _('No rollback-eligible import run was found.'))
        return redirect(redirect_route)

    outcome = rollback_run(run)
    if outcome['errors']:
        messages.warning(
            request,
            _('Rollback completed with warnings: %(count)s issue(s).') % {'count': len(outcome['errors'])}
        )
    messages.success(
        request,
        _('Rollback completed. Deleted %(deleted)s created records and restored %(restored)s updated records.') % {
            'deleted': outcome['deleted'],
            'restored': outcome['restored'],
        }
    )
    return redirect(redirect_route)


@login_required
def company_contact_remove_view(request, pk):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to remove company contacts.'))
        return redirect('companies:companyuser_list')

    contact = get_object_or_404(CompanyUser, pk=pk)
    if request.method != 'POST':
        return redirect('companies:companyuser_list')

    contact_name = contact.get_contact_name()
    contact.delete()
    messages.success(
        request,
        _('Company contact "%(name)s" was removed. User database records were not modified.') % {'name': contact_name}
    )
    return redirect('companies:companyuser_list')


@login_required
def location_company_contacts_api_view(request):
    if not _can_manage_companies(request):
        return JsonResponse({'results': []})

    company_id = request.GET.get('company')
    if not company_id:
        return JsonResponse({'results': []})

    contacts = CompanyUser.objects.filter(
        company_id=company_id,
        status=CompanyUser.UserStatus.ACTIVE,
    ).order_by('name', 'id')

    return JsonResponse({
        'results': [
            {
                'id': contact.id,
                'display_name': f"{contact.get_contact_name()} ({contact.work_email or '-'})",
            }
            for contact in contacts
        ]
    })


@login_required
@require_POST
def company_import_rollback_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to rollback imports.'))
        return redirect('companies:company_import_csv')
    return _perform_companies_rollback(request, 'company', 'companies:company_import_csv')


@login_required
@require_POST
def location_import_rollback_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to rollback imports.'))
        return redirect('companies:location_import_csv')
    return _perform_companies_rollback(request, 'location', 'companies:location_import_csv')


@login_required
@require_POST
def company_contact_import_rollback_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to rollback imports.'))
        return redirect('companies:company_contact_import_csv')
    return _perform_companies_rollback(request, 'company_contact', 'companies:company_contact_import_csv')


@login_required
def company_import_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to import companies.'))
        return redirect('companies:company_list')

    rollback_url = _companies_latest_rollback_url(request, 'company')

    if request.method == 'POST' and request.POST.get('confirm_import') == '1':
        preview_payload = _get_import_preview(request, 'company')
        if not preview_payload:
            messages.error(request, _('Import preview expired. Please upload the CSV again.'))
            return redirect('companies:company_import_csv')

        total_rows = len(preview_payload.get('rows', []))
        import_run = start_import_run(request.user, COMPANIES_IMPORT_MODULE, 'company', total_rows=total_rows)
        change_sequence = 0
        created = 0
        skipped = 0
        errors = []

        for index, row in enumerate(preview_payload.get('rows', []), start=2):
            name = _normalize_csv_cell(row.get('name'))
            code = _normalize_csv_cell(row.get('code'))
            if not name or not code:
                errors.append(_('Row %(row)s: name and code are required.') % {'row': index})
                continue

            if Company.objects.filter(Q(name__iexact=name) | Q(code__iexact=code)).exists():
                skipped += 1
                continue

            created_company = Company.objects.create(
                name=name,
                code=code,
                description=_normalize_csv_cell(row.get('description')),
                phone_number=_normalize_csv_cell(row.get('phone_number')),
                email=_normalize_csv_cell(row.get('email')),
                website=_normalize_csv_cell(row.get('website')),
                asset_prefix=_normalize_csv_cell(row.get('asset_prefix')),
                status=_normalize_csv_cell(row.get('status')) or Company.CompanyStatus.ACTIVE,
            )
            change_sequence += 1
            record_import_change(
                import_run,
                sequence=change_sequence,
                operation=ImportRunChange.ChangeOperation.CREATE,
                instance=created_company,
                row_number=index,
                after_data=snapshot_instance(created_company),
            )
            created += 1

        _clear_import_preview(request)
        finalize_import_run(
            import_run,
            created=created,
            updated=0,
            skipped=skipped,
            error_count=len(errors),
        )

        if created:
            messages.success(request, _('Imported %(count)s companies.') % {'count': created})
        if skipped:
            messages.info(request, _('Skipped %(count)s duplicate companies.') % {'count': skipped})
        return render(request, 'common/import_result.html', {
            'title': _('Company Import Result'),
            'total_rows': total_rows,
            'processed_rows': created + skipped + len(errors),
            'created': created,
            'updated': 0,
            'skipped': skipped,
            'errors': errors[:50],
            'rollback_url': reverse('companies:company_import_rollback') if import_run.can_rollback else None,
            'back_url': reverse('companies:company_list'),
        })

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.cleaned_data['file']
            try:
                reader, _encoding = _read_csv_rows_with_fallback(file_obj)
            except ValueError as exc:
                messages.error(request, str(exc))
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Companies from CSV'),
                    'form': form,
                    'back_url': reverse('companies:company_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:company_import_sample_csv'),
                    'required_columns': ['name', 'code'],
                    'optional_columns': ['description', 'phone_number', 'email', 'website', 'asset_prefix', 'status'],
                    'accepted_values_hint': _('Accepted values: status = active, inactive, suspended.'),
                })

            headers = reader.fieldnames or []
            rows = list(reader)
            if not headers:
                messages.error(request, _('CSV file is missing a header row.'))
            elif not rows:
                messages.error(request, _('CSV file has no data rows.'))
            else:
                normalized_headers, normalized_rows = _normalize_csv_headers_and_rows(headers, rows)
                _store_import_preview(request, 'company', normalized_headers, normalized_rows)
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Companies from CSV'),
                    'form': CSVImportForm(),
                    'back_url': reverse('companies:company_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:company_import_sample_csv'),
                    'required_columns': ['name', 'code'],
                    'optional_columns': ['description', 'phone_number', 'email', 'website', 'asset_prefix', 'status'],
                    'accepted_values_hint': _('Accepted values: status = active, inactive, suspended.'),
                    'preview_mode': True,
                    'preview_headers': normalized_headers,
                    'preview_matrix': _build_preview_matrix(normalized_headers, normalized_rows),
                    'preview_total_rows': len(normalized_rows),
                })
    else:
        form = CSVImportForm()

    return render(request, 'companies/import_csv.html', {
        'title': _('Import Companies from CSV'),
        'form': form,
        'back_url': reverse('companies:company_list'),
        'rollback_url': rollback_url,
        'sample_csv_url': reverse('companies:company_import_sample_csv'),
        'required_columns': ['name', 'code'],
        'optional_columns': ['description', 'phone_number', 'email', 'website', 'asset_prefix', 'status'],
        'accepted_values_hint': _('Accepted values: status = active, inactive, suspended.'),
    })


@login_required
def location_import_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to import locations.'))
        return redirect('companies:location_list')

    rollback_url = _companies_latest_rollback_url(request, 'location')

    if request.method == 'POST' and request.POST.get('confirm_import') == '1':
        preview_payload = _get_import_preview(request, 'location')
        if not preview_payload:
            messages.error(request, _('Import preview expired. Please upload the CSV again.'))
            return redirect('companies:location_import_csv')

        total_rows = len(preview_payload.get('rows', []))
        import_run = start_import_run(request.user, COMPANIES_IMPORT_MODULE, 'location', total_rows=total_rows)
        change_sequence = 0
        update_existing = request.POST.get('update_existing') == '1'
        created = 0
        updated = 0
        skipped = 0
        errors = []
        skip_reasons = []
        update_changes = []

        valid_location_types = {choice[0] for choice in Location.LocationType.choices}
        valid_statuses = {choice[0] for choice in Location.LocationStatus.choices}

        for index, row in enumerate(preview_payload.get('rows', []), start=2):
            company_lookup = _normalize_csv_cell(row.get('company'))
            name = _normalize_csv_cell(row.get('name'))
            code = _normalize_csv_cell(row.get('code')) or None
            if not company_lookup or not name:
                errors.append(_('Row %(row)s: company and name are required.') % {'row': index})
                continue

            company = Company.objects.filter(Q(code__iexact=company_lookup) | Q(name__iexact=company_lookup)).first()
            if not company:
                errors.append(_('Row %(row)s: company "%(company)s" not found.') % {'row': index, 'company': company_lookup})
                continue

            existing_location = None
            if code:
                existing_location = Location.objects.filter(company=company, code=code).first()
            else:
                existing_location = Location.objects.filter(
                    company=company,
                    name__iexact=name,
                ).filter(Q(code__isnull=True) | Q(code='')).first()

            location_type = _normalize_csv_cell(row.get('location_type')) or Location.LocationType.OTHER
            if location_type not in valid_location_types:
                errors.append(
                    _('Row %(row)s: invalid location_type "%(value)s".') % {
                        'row': index,
                        'value': _normalize_csv_cell(row.get('location_type')),
                    }
                )
                continue

            status = _normalize_csv_cell(row.get('status')) or Location.LocationStatus.ACTIVE
            if status not in valid_statuses:
                errors.append(
                    _('Row %(row)s: invalid status "%(value)s".') % {
                        'row': index,
                        'value': _normalize_csv_cell(row.get('status')),
                    }
                )
                continue

            contact = None
            contact_email = _normalize_csv_cell(row.get('contact_email')).lower()
            contact_name = _normalize_csv_cell(row.get('contact_name'))
            contact_phone = _normalize_csv_cell(row.get('contact_phone'))

            if contact_email:
                contact = CompanyUser.objects.filter(
                    company=company,
                    work_email__iexact=contact_email,
                ).first()

            if not contact and contact_name:
                contact_query = CompanyUser.objects.filter(
                    company=company,
                    name__iexact=contact_name,
                )
                if contact_phone:
                    contact_query = contact_query.filter(work_phone=contact_phone)
                contact = contact_query.first()

            if not contact and (contact_email or contact_name or contact_phone):
                fallback_name = contact_name or (contact_email.split('@')[0] if contact_email else _('Location Contact'))
                contact = CompanyUser.objects.create(
                    company=company,
                    name=fallback_name,
                    role=CompanyUser.CompanyRole.EMPLOYEE,
                    status=CompanyUser.UserStatus.ACTIVE,
                    work_email=contact_email,
                    work_phone=contact_phone,
                )
                change_sequence += 1
                record_import_change(
                    import_run,
                    sequence=change_sequence,
                    operation=ImportRunChange.ChangeOperation.CREATE,
                    instance=contact,
                    row_number=index,
                    after_data=snapshot_instance(contact),
                )

            payload = {
                'name': name,
                'name_en': _normalize_csv_cell(row.get('name_en')),
                'code': code,
                'code_2': _normalize_csv_cell(row.get('code_2')),
                'description': _normalize_csv_cell(row.get('description')),
                'location_type': location_type,
                'status': status,
                'zone': _normalize_csv_cell(row.get('zone')) or None,
                'rack': _normalize_csv_cell(row.get('rack')) or None,
                'shelf': _normalize_csv_cell(row.get('shelf')) or None,
                'address_line1': _normalize_csv_cell(row.get('address_line1')),
                'address_line2': _normalize_csv_cell(row.get('address_line2')),
                'city': _normalize_csv_cell(row.get('city')),
                'state_province': _normalize_csv_cell(row.get('state_province')),
                'postal_code': _normalize_csv_cell(row.get('postal_code')),
                'country': _normalize_csv_cell(row.get('country')),
                'chinese_address': _normalize_csv_cell(row.get('chinese_address')),
                'contact': contact,
                'email': _normalize_csv_cell(row.get('email')),
                'phone_number': _normalize_csv_cell(row.get('phone_number')),
            }

            if existing_location:
                if not update_existing:
                    skipped += 1
                    skip_reasons.append(
                        _('Row %(row)s: duplicate location match found (%(identifier)s); skipped.') % {
                            'row': index,
                            'identifier': existing_location.code or existing_location.name,
                        }
                    )
                    continue

                changed_fields = []
                before_snapshot = snapshot_instance(existing_location)
                for field_name, new_value in payload.items():
                    old_value = getattr(existing_location, field_name)
                    if old_value != new_value:
                        changed_fields.append({
                            'field': field_name,
                            'old': '' if old_value is None else str(old_value),
                            'new': '' if new_value is None else str(new_value),
                        })
                        setattr(existing_location, field_name, new_value)

                if changed_fields:
                    existing_location.save()
                    change_sequence += 1
                    record_import_change(
                        import_run,
                        sequence=change_sequence,
                        operation=ImportRunChange.ChangeOperation.UPDATE,
                        instance=existing_location,
                        row_number=index,
                        before_data=before_snapshot,
                        after_data=snapshot_instance(existing_location),
                    )
                    updated += 1
                    update_changes.append({
                        'row': index,
                        'identifier': existing_location.code or existing_location.name,
                        'changes': changed_fields,
                    })
                else:
                    skipped += 1
                    skip_reasons.append(
                        _('Row %(row)s: duplicate found but no field changes detected.') % {'row': index}
                    )
                continue

            created_location = Location.objects.create(company=company, **payload)
            change_sequence += 1
            record_import_change(
                import_run,
                sequence=change_sequence,
                operation=ImportRunChange.ChangeOperation.CREATE,
                instance=created_location,
                row_number=index,
                after_data=snapshot_instance(created_location),
            )
            created += 1

        _clear_import_preview(request)
        finalize_import_run(
            import_run,
            created=created,
            updated=updated,
            skipped=skipped,
            error_count=len(errors),
        )

        if created:
            messages.success(request, _('Imported %(count)s locations.') % {'count': created})
        if updated:
            messages.success(request, _('Updated %(count)s existing locations.') % {'count': updated})
        if skipped:
            messages.info(request, _('Skipped %(count)s duplicate locations.') % {'count': skipped})

        issues = errors[:30] + skip_reasons[:30]
        return render(request, 'common/import_result.html', {
            'title': _('Location Import Result'),
            'total_rows': total_rows,
            'processed_rows': created + updated + skipped + len(errors),
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'errors': errors[:50],
            'issues': issues,
            'update_changes': update_changes[:30],
            'rollback_url': reverse('companies:location_import_rollback') if import_run.can_rollback else None,
            'back_url': reverse('companies:location_list'),
        })

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.cleaned_data['file']
            try:
                reader, _encoding = _read_csv_rows_with_fallback(file_obj)
            except ValueError as exc:
                messages.error(request, str(exc))
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Locations from CSV'),
                    'form': form,
                    'back_url': reverse('companies:location_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:location_import_sample_csv'),
                    'required_columns': ['company', 'name'],
                    'optional_columns': [
                        'name_en', 'code', 'code_2', 'description', 'location_type', 'status',
                        'zone', 'rack', 'shelf', 'address_line1', 'address_line2', 'city',
                        'state_province', 'postal_code', 'country', 'chinese_address',
                        'email', 'phone_number', 'contact_email', 'contact_name', 'contact_phone'
                    ],
                    'accepted_values_hint': _('Accepted values: location_type = warehouse, office, store, other; status = active, closed, under_construction. Contact can be matched by contact_email or contact_name/contact_phone; unmatched contacts are created in company contacts.'),
                })

            headers = reader.fieldnames or []
            rows = list(reader)
            if not headers:
                messages.error(request, _('CSV file is missing a header row.'))
            elif not rows:
                messages.error(request, _('CSV file has no data rows.'))
            else:
                normalized_headers, normalized_rows = _normalize_csv_headers_and_rows(headers, rows)
                _store_import_preview(request, 'location', normalized_headers, normalized_rows)
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Locations from CSV'),
                    'form': CSVImportForm(),
                    'back_url': reverse('companies:location_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:location_import_sample_csv'),
                    'required_columns': ['company', 'name'],
                    'optional_columns': [
                        'name_en', 'code', 'code_2', 'description', 'location_type', 'status',
                        'zone', 'rack', 'shelf', 'address_line1', 'address_line2', 'city',
                        'state_province', 'postal_code', 'country', 'chinese_address',
                        'email', 'phone_number', 'contact_email', 'contact_name', 'contact_phone'
                    ],
                    'accepted_values_hint': _('Accepted values: location_type = warehouse, office, store, other; status = active, closed, under_construction. Contact can be matched by contact_email or contact_name/contact_phone; unmatched contacts are created in company contacts.'),
                    'preview_mode': True,
                    'show_update_existing': True,
                    'preview_headers': normalized_headers,
                    'preview_matrix': _build_preview_matrix(normalized_headers, normalized_rows),
                    'preview_total_rows': len(normalized_rows),
                })
    else:
        form = CSVImportForm()

    return render(request, 'companies/import_csv.html', {
        'title': _('Import Locations from CSV'),
        'form': form,
        'back_url': reverse('companies:location_list'),
        'rollback_url': rollback_url,
        'sample_csv_url': reverse('companies:location_import_sample_csv'),
        'required_columns': ['company', 'name'],
        'optional_columns': [
            'name_en', 'code', 'code_2', 'description', 'location_type', 'status',
            'zone', 'rack', 'shelf', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country', 'chinese_address',
            'email', 'phone_number', 'contact_email', 'contact_name', 'contact_phone'
        ],
        'accepted_values_hint': _('Accepted values: location_type = warehouse, office, store, other; status = active, closed, under_construction. Contact can be matched by contact_email or contact_name/contact_phone; unmatched contacts are created in company contacts.'),
    })


@login_required
def company_contact_import_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to import company contacts.'))
        return redirect('companies:companyuser_list')

    rollback_url = _companies_latest_rollback_url(request, 'company_contact')

    if request.method == 'POST' and request.POST.get('confirm_import') == '1':
        preview_payload = _get_import_preview(request, 'company_contact')
        if not preview_payload:
            messages.error(request, _('Import preview expired. Please upload the CSV again.'))
            return redirect('companies:company_contact_import_csv')

        total_rows = len(preview_payload.get('rows', []))
        import_run = start_import_run(request.user, COMPANIES_IMPORT_MODULE, 'company_contact', total_rows=total_rows)
        change_sequence = 0
        created = 0
        skipped = 0
        errors = []

        valid_roles = {choice[0] for choice in CompanyUser.CompanyRole.choices}
        valid_statuses = {choice[0] for choice in CompanyUser.UserStatus.choices}

        for index, row in enumerate(preview_payload.get('rows', []), start=2):
            company_lookup = _normalize_csv_cell(row.get('company'))
            name = _normalize_csv_cell(row.get('name'))
            if not company_lookup or not name:
                errors.append(_('Row %(row)s: company and name are required.') % {'row': index})
                continue

            company = Company.objects.filter(Q(code__iexact=company_lookup) | Q(name__iexact=company_lookup)).first()
            if not company:
                errors.append(_('Row %(row)s: company "%(company)s" not found.') % {'row': index, 'company': company_lookup})
                continue

            work_email = _normalize_csv_cell(row.get('work_email'))
            duplicate_query = CompanyUser.objects.filter(company=company, name__iexact=name)
            if work_email:
                duplicate_query = duplicate_query.filter(work_email__iexact=work_email)
            if duplicate_query.exists():
                skipped += 1
                continue

            role = _normalize_csv_cell(row.get('role')) or CompanyUser.CompanyRole.EMPLOYEE
            if role not in valid_roles:
                errors.append(
                    _('Row %(row)s: invalid role "%(value)s".') % {
                        'row': index,
                        'value': _normalize_csv_cell(row.get('role')),
                    }
                )
                continue

            status = _normalize_csv_cell(row.get('status')) or CompanyUser.UserStatus.ACTIVE
            if status not in valid_statuses:
                errors.append(
                    _('Row %(row)s: invalid status "%(value)s".') % {
                        'row': index,
                        'value': _normalize_csv_cell(row.get('status')),
                    }
                )
                continue

            location_name = _normalize_csv_cell(row.get('location'))
            location = None
            if location_name:
                location = Location.objects.filter(company=company, name__iexact=location_name).first()

            linked_user = None
            if work_email:
                linked_user = User.objects.filter(email__iexact=work_email).first()
            work_phone = _normalize_csv_cell(row.get('work_phone'))
            if linked_user and not work_phone:
                work_phone = linked_user.phone_number or ''

            created_contact = CompanyUser.objects.create(
                user=linked_user,
                name=name,
                company=company,
                location=location,
                role=role,
                status=status,
                employee_id=_normalize_csv_cell(row.get('employee_id')),
                department=_normalize_csv_cell(row.get('department')),
                job_title=_normalize_csv_cell(row.get('job_title')),
                work_phone=work_phone,
                work_email=work_email,
            )
            change_sequence += 1
            record_import_change(
                import_run,
                sequence=change_sequence,
                operation=ImportRunChange.ChangeOperation.CREATE,
                instance=created_contact,
                row_number=index,
                after_data=snapshot_instance(created_contact),
            )
            created += 1

        _clear_import_preview(request)
        finalize_import_run(
            import_run,
            created=created,
            updated=0,
            skipped=skipped,
            error_count=len(errors),
        )

        if created:
            messages.success(request, _('Imported %(count)s company contacts.') % {'count': created})
        if skipped:
            messages.info(request, _('Skipped %(count)s duplicate company contacts.') % {'count': skipped})
        return render(request, 'common/import_result.html', {
            'title': _('Company Contact Import Result'),
            'total_rows': total_rows,
            'processed_rows': created + skipped + len(errors),
            'created': created,
            'updated': 0,
            'skipped': skipped,
            'errors': errors[:50],
            'rollback_url': reverse('companies:company_contact_import_rollback') if import_run.can_rollback else None,
            'back_url': reverse('companies:companyuser_list'),
        })

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.cleaned_data['file']
            try:
                reader, _encoding = _read_csv_rows_with_fallback(file_obj)
            except ValueError as exc:
                messages.error(request, str(exc))
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Company Contacts from CSV'),
                    'form': form,
                    'back_url': reverse('companies:companyuser_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:company_contact_import_sample_csv'),
                    'required_columns': ['company', 'name'],
                    'optional_columns': [
                        'role', 'status', 'location', 'employee_id', 'department',
                        'job_title', 'work_phone', 'work_email'
                    ],
                    'accepted_values_hint': _('Accepted values: role = employee, manager, admin, viewer; status = active, inactive, suspended.'),
                })

            headers = reader.fieldnames or []
            rows = list(reader)
            if not headers:
                messages.error(request, _('CSV file is missing a header row.'))
            elif not rows:
                messages.error(request, _('CSV file has no data rows.'))
            else:
                normalized_headers, normalized_rows = _normalize_csv_headers_and_rows(headers, rows)
                _store_import_preview(request, 'company_contact', normalized_headers, normalized_rows)
                return render(request, 'companies/import_csv.html', {
                    'title': _('Import Company Contacts from CSV'),
                    'form': CSVImportForm(),
                    'back_url': reverse('companies:companyuser_list'),
                    'rollback_url': rollback_url,
                    'sample_csv_url': reverse('companies:company_contact_import_sample_csv'),
                    'required_columns': ['company', 'name'],
                    'optional_columns': [
                        'role', 'status', 'location', 'employee_id', 'department',
                        'job_title', 'work_phone', 'work_email'
                    ],
                    'accepted_values_hint': _('Accepted values: role = employee, manager, admin, viewer; status = active, inactive, suspended.'),
                    'preview_mode': True,
                    'preview_headers': normalized_headers,
                    'preview_matrix': _build_preview_matrix(normalized_headers, normalized_rows),
                    'preview_total_rows': len(normalized_rows),
                })
    else:
        form = CSVImportForm()

    return render(request, 'companies/import_csv.html', {
        'title': _('Import Company Contacts from CSV'),
        'form': form,
        'back_url': reverse('companies:companyuser_list'),
        'rollback_url': rollback_url,
        'sample_csv_url': reverse('companies:company_contact_import_sample_csv'),
        'required_columns': ['company', 'name'],
        'optional_columns': [
            'role', 'status', 'location', 'employee_id', 'department',
            'job_title', 'work_phone', 'work_email'
        ],
        'accepted_values_hint': _('Accepted values: role = employee, manager, admin, viewer; status = active, inactive, suspended.'),
    })


@login_required
def company_import_sample_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to download sample files.'))
        return redirect('companies:company_list')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_import_sample.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'name (required)', 'code (required)', 'description (optional)',
        'phone_number (optional)', 'email (optional)', 'website (optional)',
        'asset_prefix (optional)', 'status (optional)'
    ])
    writer.writerows([
        ['Acme Trading', 'ACME', 'Main trading entity', '+8613800000001', 'contact@acme.com', 'https://acme.com', 'AC-', 'active'],
        ['North Branch', 'NORTH', 'Regional branch office', '+8613800000002', 'north@acme.com', 'https://north.acme.com', 'NB-', 'active'],
        ['South Distribution', 'SOUTH', 'South distribution center', '+8613800000003', 'south@acme.com', 'https://south.acme.com', 'SD-', 'inactive'],
        ['East Retail', 'EAST', 'Retail storefront operation', '+8613800000004', 'east@acme.com', 'https://east.acme.com', 'ER-', 'active'],
        ['West Logistics', 'WEST', 'Logistics and transport hub', '+8613800000005', 'west@acme.com', 'https://west.acme.com', 'WL-', 'suspended'],
        ['Central Office', 'CENTRAL', 'Corporate headquarters', '+8613800000006', 'hq@acme.com', 'https://hq.acme.com', 'CO-', 'active'],
        ['Import Services', 'IMPORT', 'International sourcing unit', '+8613800000007', 'import@acme.com', 'https://import.acme.com', 'IM-', 'active'],
        ['Export Services', 'EXPORT', 'Overseas shipping unit', '+8613800000008', 'export@acme.com', 'https://export.acme.com', 'EX-', 'inactive'],
        ['Online Commerce', 'ECOM', 'E-commerce operations team', '+8613800000009', 'ecom@acme.com', 'https://shop.acme.com', 'EC-', 'active'],
        ['Service Center', 'SERVICE', 'After-sales service division', '+8613800000010', 'service@acme.com', 'https://service.acme.com', 'SV-', 'active'],
    ])
    return response


@login_required
def location_import_sample_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to download sample files.'))
        return redirect('companies:location_list')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="location_import_sample.csv"'

    writer = csv.writer(response)
    columns = [
        'company', 'name', 'name_en', 'code', 'code_2', 'description',
        'location_type', 'status', 'zone', 'rack', 'shelf',
        'address_line1', 'address_line2', 'city', 'state_province',
        'postal_code', 'country', 'chinese_address', 'email', 'phone_number',
        'contact_email', 'contact_name', 'contact_phone'
    ]
    writer.writerow([
        'company (required)', 'name (required)', 'name_en (optional)',
        'code (optional)', 'code_2 (optional)', 'description (optional)',
        'location_type (optional)', 'status (optional)', 'zone (optional)',
        'rack (optional)', 'shelf (optional)', 'address_line1 (optional)',
        'address_line2 (optional)', 'city (optional)',
        'state_province (optional)', 'postal_code (optional)', 'country (optional)',
        'chinese_address (optional)', 'email (optional)', 'phone_number (optional)',
        'contact_email (optional)', 'contact_name (optional)', 'contact_phone (optional)'
    ])

    sample_rows = [
        {'company': 'ACME', 'name': '主仓库', 'name_en': 'Main Warehouse', 'code': 'WH-01', 'code_2': 'WH-A', 'description': 'Central warehouse', 'location_type': 'warehouse', 'status': 'active', 'zone': 'Z1', 'rack': 'R1', 'shelf': 'S1', 'address_line1': '100 Logistics Rd', 'address_line2': '', 'city': 'Shanghai', 'state_province': 'Shanghai', 'postal_code': '200000', 'country': 'China', 'chinese_address': '上海市浦东新区物流路100号', 'email': 'warehouse@acme.com', 'phone_number': '+8613800001001', 'contact_email': 'leo.yao@acme.com', 'contact_name': 'Leo Yao', 'contact_phone': '+8613700000001'},
        {'company': 'NORTH', 'name': '北区仓', 'name_en': 'North Storage', 'code': 'WH-02', 'code_2': 'WH-B', 'description': 'North inventory site', 'location_type': 'warehouse', 'status': 'active', 'zone': 'Z2', 'rack': 'R2', 'shelf': 'S2', 'address_line1': '200 North Rd', 'address_line2': '', 'city': 'Beijing', 'state_province': 'Beijing', 'postal_code': '100000', 'country': 'China', 'chinese_address': '北京市朝阳区北路200号', 'email': 'north.storage@north.com', 'phone_number': '+8613800001002', 'contact_email': 'mina.chen@north.com', 'contact_name': 'Mina Chen', 'contact_phone': '+8613700000002'},
        {'company': 'SOUTH', 'name': '南区分拨', 'name_en': 'South Dispatch', 'code': '', 'code_2': 'WH-C', 'description': 'South dispatch site', 'location_type': 'warehouse', 'status': 'closed', 'zone': 'Z3', 'rack': 'R3', 'shelf': 'S3', 'address_line1': '300 South Rd', 'address_line2': '', 'city': 'Guangzhou', 'state_province': 'Guangdong', 'postal_code': '510000', 'country': 'China', 'chinese_address': '广州市天河区南路300号', 'email': 'dispatch@south.com', 'phone_number': '+8613800001003', 'contact_email': 'kai.lin@south.com', 'contact_name': 'Kai Lin', 'contact_phone': '+8613700000003'},
        {'company': 'EAST', 'name': '东区办公室', 'name_en': 'East Office', 'code': 'OFF-01', 'code_2': 'OFF-E1', 'description': 'Sales and admin office', 'location_type': 'office', 'status': 'active', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '88 Business St', 'address_line2': 'Suite 5', 'city': 'Shanghai', 'state_province': 'Shanghai', 'postal_code': '200001', 'country': 'China', 'chinese_address': '上海市静安区商务街88号5室', 'email': 'office@east.com', 'phone_number': '+8613800001004', 'contact_email': 'iris.tan@east.com', 'contact_name': 'Iris Tan', 'contact_phone': '+8613700000004'},
        {'company': 'WEST', 'name': '西区办公室', 'name_en': 'West Office', 'code': '', 'code_2': 'OFF-W1', 'description': 'Regional support office', 'location_type': 'office', 'status': 'under_construction', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '12 Harbor Ave', 'address_line2': 'Floor 3', 'city': 'Shenzhen', 'state_province': 'Guangdong', 'postal_code': '518000', 'country': 'China', 'chinese_address': '深圳市南山区港湾大道12号3层', 'email': 'support@west.com', 'phone_number': '+8613800001005', 'contact_email': 'noah.wu@west.com', 'contact_name': 'Noah Wu', 'contact_phone': '+8613700000005'},
        {'company': 'CENTRAL', 'name': '中央门店', 'name_en': 'Central Storefront', 'code': 'STR-01', 'code_2': 'STR-C1', 'description': 'Customer pickup store', 'location_type': 'store', 'status': 'active', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '66 Market Ave', 'address_line2': '', 'city': 'Chengdu', 'state_province': 'Sichuan', 'postal_code': '610000', 'country': 'China', 'chinese_address': '成都市锦江区市场大道66号', 'email': 'store@central.com', 'phone_number': '+8613800001006', 'contact_email': 'ava.guo@central.com', 'contact_name': 'Ava Guo', 'contact_phone': '+8613700000006'},
        {'company': 'IMPORT', 'name': '进口门店', 'name_en': 'Import Store', 'code': '', 'code_2': 'STR-I1', 'description': 'Import retail store', 'location_type': 'store', 'status': 'active', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '55 Port Rd', 'address_line2': '', 'city': 'Ningbo', 'state_province': 'Zhejiang', 'postal_code': '315000', 'country': 'China', 'chinese_address': '宁波市北仑区港口路55号', 'email': 'import.store@import.com', 'phone_number': '+8613800001007', 'contact_email': 'ethan.qiu@import.com', 'contact_name': 'Ethan Qiu', 'contact_phone': '+8613700000007'},
        {'company': 'EXPORT', 'name': '出口门店', 'name_en': 'Export Store', 'code': 'STR-03', 'code_2': 'STR-E1', 'description': 'Export retail store', 'location_type': 'store', 'status': 'closed', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '9 Terminal Rd', 'address_line2': '', 'city': 'Tianjin', 'state_province': 'Tianjin', 'postal_code': '300000', 'country': 'China', 'chinese_address': '天津市滨海新区码头路9号', 'email': 'export.store@export.com', 'phone_number': '+8613800001008', 'contact_email': 'luna.fang@export.com', 'contact_name': 'Luna Fang', 'contact_phone': '+8613700000008'},
        {'company': 'ECOM', 'name': '电商分拣中心', 'name_en': 'Ecom Fulfillment', 'code': 'FUL-01', 'code_2': 'FUL-E1', 'description': 'Online order fulfillment', 'location_type': 'other', 'status': 'active', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '18 Digital Park', 'address_line2': 'Building B', 'city': 'Hangzhou', 'state_province': 'Zhejiang', 'postal_code': '310000', 'country': 'China', 'chinese_address': '杭州市余杭区数字园18号B栋', 'email': 'fulfillment@ecom.com', 'phone_number': '+8613800001009', 'contact_email': 'owen.he@ecom.com', 'contact_name': 'Owen He', 'contact_phone': '+8613700000009'},
        {'company': 'SERVICE', 'name': '维修中心', 'name_en': 'Repair Center', 'code': '', 'code_2': 'SRV-S1', 'description': 'After-sales service location', 'location_type': 'other', 'status': 'active', 'zone': '', 'rack': '', 'shelf': '', 'address_line1': '77 Service Rd', 'address_line2': '', 'city': 'Wuhan', 'state_province': 'Hubei', 'postal_code': '430000', 'country': 'China', 'chinese_address': '武汉市洪山区服务路77号', 'email': 'service.center@service.com', 'phone_number': '+8613800001010', 'contact_email': 'nora.dai@service.com', 'contact_name': 'Nora Dai', 'contact_phone': '+8613700000010'},
    ]
    for row in sample_rows:
        writer.writerow([row.get(column, '') for column in columns])
    return response


@login_required
def company_contact_import_sample_csv_view(request):
    if not _can_manage_companies(request):
        messages.error(request, _('You do not have permission to download sample files.'))
        return redirect('companies:companyuser_list')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_contact_import_sample.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'company (required)', 'name (required)', 'role (optional)', 'status (optional)',
        'location (optional)', 'employee_id (optional)', 'department (optional)',
        'job_title (optional)', 'work_phone (optional)', 'work_email (optional)'
    ])
    writer.writerows([
        ['ACME', 'Leo Yao', 'admin', 'active', 'Main Warehouse', 'E-1001', 'Operations', 'Operations Lead', '+8613700000001', 'leo.yao@acme.com'],
        ['NORTH', 'Mina Chen', 'manager', 'active', 'North Storage', 'E-1002', 'Warehouse', 'Warehouse Manager', '+8613700000002', 'mina.chen@north.com'],
        ['SOUTH', 'Kai Lin', 'employee', 'active', 'South Dispatch', 'E-1003', 'Dispatch', 'Dispatch Clerk', '+8613700000003', 'kai.lin@south.com'],
        ['EAST', 'Iris Tan', 'viewer', 'inactive', 'East Office', 'E-1004', 'Sales', 'Sales Assistant', '+8613700000004', 'iris.tan@east.com'],
        ['WEST', 'Noah Wu', 'employee', 'active', 'West Office', 'E-1005', 'Support', 'Support Specialist', '+8613700000005', 'noah.wu@west.com'],
        ['CENTRAL', 'Ava Guo', 'manager', 'suspended', 'Central Storefront', 'E-1006', 'Retail', 'Store Manager', '+8613700000006', 'ava.guo@central.com'],
        ['IMPORT', 'Ethan Qiu', 'employee', 'active', 'Import Hub', 'E-1007', 'Procurement', 'Import Coordinator', '+8613700000007', 'ethan.qiu@import.com'],
        ['EXPORT', 'Luna Fang', 'employee', 'inactive', 'Export Yard', 'E-1008', 'Shipping', 'Export Specialist', '+8613700000008', 'luna.fang@export.com'],
        ['ECOM', 'Owen He', 'viewer', 'active', 'Ecom Fulfillment', 'E-1009', 'E-Commerce', 'Order Analyst', '+8613700000009', 'owen.he@ecom.com'],
        ['SERVICE', 'Nora Dai', 'admin', 'active', 'Repair Center', 'E-1010', 'Service', 'Service Supervisor', '+8613700000010', 'nora.dai@service.com'],
    ])
    return response
