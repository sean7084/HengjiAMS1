"""
Forms for the inspections web UI.

Covers batch creation (by-brand auto-spread + schedule upload), asset-list
export filtering, and the inspection list filter sidebar.
"""
import re
from datetime import date, timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from companies.models import Company, Division, Location
from inspections.models import InspectionBatch, StoreInspection

User = get_user_model()

# Accept both .xlsx and .csv for schedule/asset uploads (matches the importer).
_UPLOAD_EXTS = ('.xlsx', '.xls', '.csv')
_WEEK_PATTERN = re.compile(r'^\s*(\d{4})-?W?(\d{1,2})\s*$', re.IGNORECASE)


def _validate_upload_extension(value):
    name = (value.name or '').lower()
    if not name.endswith(_UPLOAD_EXTS):
        raise forms.ValidationError(
            _('Unsupported file type. Upload an .xlsx, .xls, or .csv file.')
        )


class InspectionBatchByBrandForm(forms.ModelForm):
    """Create a batch by picking a brand + date range; stores auto-spread."""

    class Meta:
        model = InspectionBatch
        fields = ['name', 'company', 'division', 'engineer', 'start_date', 'end_date', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g. Gucci August 2026 Rollout'),
            }),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'engineer': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields['company'].queryset = user.get_accessible_companies()
            self.fields['engineer'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name', 'username')
            # Limit divisions to those the user can access (superadmin sees all).
            self.fields['division'].queryset = user.get_accessible_divisions()
        else:
            self.fields['company'].queryset = Company.objects.all()
            self.fields['division'].queryset = Division.objects.all()
            self.fields['engineer'].queryset = User.objects.filter(is_active=True)

        # Default the date range to "today .. today+13" (a two-week window) on
        # create only; on update the instance's values take precedence.
        if not self.is_bound and not self.instance.pk:
            today = date.today()
            self.fields['start_date'].initial = today
            self.fields['end_date'].initial = today + timedelta(days=13)

    def clean(self):
        cleaned = super().clean()
        company = cleaned.get('company')
        division = cleaned.get('division')
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')

        if division and company and division.company_id != company.id:
            self.add_error('division', _('The selected brand does not belong to the chosen company.'))

        if start and end and end < start:
            self.add_error('end_date', _('End date must be on or after the start date.'))

        return cleaned

    def clean_division(self):
        division = self.cleaned_data.get('division')
        if division is None:
            raise forms.ValidationError(_('Select a brand to schedule inspections for.'))
        return division


class ScheduleImportForm(forms.Form):
    """Upload a schedule.xlsx (and optional asset_list.xlsx) to create a batch."""

    name = forms.CharField(
        max_length=200,
        label=_('Batch Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g. Kering 2026 W34 Master Import'),
        }),
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label=_('Company'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    schedule_file = forms.FileField(
        label=_('Schedule File'),
        help_text=_('Excel/CSV with columns: Brand, Store Name, JDA code, inspection_date.'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls,.csv'}),
        validators=[_validate_upload_extension],
    )
    assets_file = forms.FileField(
        label=_('Master Asset List (optional)'),
        required=False,
        help_text=_('Excel/CSV with per-store device rows. Leave blank for a schedule-only import.'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls,.csv'}),
        validators=[_validate_upload_extension],
    )
    engineer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_('Default Engineer'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields['company'].queryset = user.get_accessible_companies()
            self.fields['engineer'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name', 'username')


class AssetListExportForm(forms.Form):
    """Filter the cross-store asset-list export.

    At least one of batch / division / date range / ISO week must be supplied so
    the export does not accidentally dump the entire database.
    """

    batch = forms.ModelChoiceField(
        queryset=InspectionBatch.objects.all(),
        label=_('Batch'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    division = forms.ModelChoiceField(
        queryset=Division.objects.all(),
        label=_('Brand / Division'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        label=_('From'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to = forms.DateField(
        label=_('To'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    week = forms.CharField(
        label=_('ISO Week'),
        required=False,
        max_length=10,
        help_text=_('e.g. 2026-W05 or 2026W5. Overrides the date range when set.'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2026-W05'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields['batch'].queryset = InspectionBatch.objects.filter(
                company__in=user.get_accessible_companies()
            )
            self.fields['division'].queryset = user.get_accessible_divisions()

    def clean_week(self):
        raw = (self.cleaned_data.get('week') or '').strip()
        if not raw:
            return None
        match = _WEEK_PATTERN.match(raw)
        if not match:
            raise forms.ValidationError(_('Enter an ISO week as YYYY-Www (e.g. 2026-W05).'))
        year = int(match.group(1))
        week = int(match.group(2))
        if not (1 <= week <= 53):
            raise forms.ValidationError(_('Week number must be between 1 and 53.'))
        # Validate the week actually exists in that ISO year.
        try:
            date.fromisocalendar(year, week, 1)
        except ValueError:
            raise forms.ValidationError(
                _('Week %(week)s does not exist in ISO year %(year)s.') % {'week': week, 'year': year}
            )
        return (year, week)

    def clean(self):
        cleaned = super().clean()
        if not any([
            cleaned.get('batch'), cleaned.get('division'),
            cleaned.get('date_from'), cleaned.get('date_to'), cleaned.get('week'),
        ]):
            raise forms.ValidationError(
                _('Select at least one filter (batch, brand, date range, or ISO week).')
            )
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        if date_from and date_to and date_to < date_from:
            self.add_error('date_to', _('"To" date must be on or after "From" date.'))
        return cleaned

    def resolve_inspections(self):
        """Return the StoreInspection queryset matching the cleaned filters."""
        qs = StoreInspection.objects.select_related('batch', 'division', 'location', 'engineer')

        batch = self.cleaned_data.get('batch')
        division = self.cleaned_data.get('division')
        date_from = self.cleaned_data.get('date_from')
        date_to = self.cleaned_data.get('date_to')
        week = self.cleaned_data.get('week')

        if batch:
            qs = qs.filter(batch=batch)
        if division:
            qs = qs.filter(division=division)

        if week:
            iso_year, iso_week = week
            monday = date.fromisocalendar(iso_year, iso_week, 1)
            sunday = monday + timedelta(days=6)
            qs = qs.filter(inspection_date__gte=monday, inspection_date__lte=sunday)
        else:
            if date_from:
                qs = qs.filter(inspection_date__gte=date_from)
            if date_to:
                qs = qs.filter(inspection_date__lte=date_to)

        return qs.order_by('inspection_date', 'jda_code')


class StoreInspectionFilterForm(forms.Form):
    """GET filters for the inspection list view."""

    batch = forms.ModelChoiceField(
        queryset=InspectionBatch.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    division = forms.ModelChoiceField(
        queryset=Division.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    status = forms.ChoiceField(
        choices=[('', _('All statuses'))] + list(StoreInspection.Status.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    engineer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': _('Search store label, JDA, or store name'),
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields['batch'].queryset = InspectionBatch.objects.filter(
                company__in=user.get_accessible_companies()
            )
            self.fields['division'].queryset = user.get_accessible_divisions()
