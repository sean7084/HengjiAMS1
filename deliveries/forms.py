"""Forms for delivery order workflow."""

from django import forms

from assets.models import Asset

from .models import DeliveryOrder


class DeliveryOrderForm(forms.ModelForm):
    """Create/update delivery order and choose dispatch assets."""

    selected_assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label='Assets to Dispatch',
    )

    class Meta:
        model = DeliveryOrder
        fields = [
            'delivery_date',
            'receiver_name',
            'receiver_phone',
            'delivery_address',
            'delivery_method',
            'remarks',
        ]

    def __init__(self, *args, quotation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.quotation = quotation

        if quotation is not None:
            self.fields['selected_assets'].queryset = Asset.objects.filter(
                source_quotation=quotation,
                status=Asset.AssetStatus.AVAILABLE,
            ).select_related('brand', 'model').order_by('asset_number')
            self.fields['selected_assets'].label_from_instance = (
                lambda obj: f"{obj.asset_number} - {obj.serial_number} - "
                f"{obj.brand.name if obj.brand else '-'} - {obj.description or '-'}"
            )


class SignedCopyUploadForm(forms.ModelForm):
    """Upload signed delivery copy."""

    class Meta:
        model = DeliveryOrder
        fields = ['signed_file']

    def clean_signed_file(self):
        file_obj = self.cleaned_data.get('signed_file')
        if not file_obj:
            return file_obj

        allowed_exts = {'.pdf', '.jpg', '.jpeg', '.png'}
        filename = file_obj.name.lower()
        if not any(filename.endswith(ext) for ext in allowed_exts):
            raise forms.ValidationError('Invalid file type. Allowed: PDF, JPG, JPEG, PNG.')

        return file_obj
