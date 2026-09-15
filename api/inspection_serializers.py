"""
Serializers for the Kering store-inspection mini-program API.

Kept in a dedicated module (rather than api/serializers.py) to avoid bloating the
core asset API, while following the project's convention of centralizing the REST
surface in the `api` app.
"""
from rest_framework import serializers

from inspections.models import (
    InspectionDevice,
    InspectionIssue,
    InspectionPhoto,
    StoreInspection,
)


class InspectionPhotoSerializer(serializers.ModelSerializer):
    """A captured photo (device overall/serial or rack/network/issue)."""

    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = InspectionPhoto
        fields = [
            'id', 'kind', 'device', 'image', 'client_photo_uid', 'display_name',
            'sort_index', 'captured_at', 'uploaded_by', 'uploaded_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'display_name', 'uploaded_by', 'created_at']


class InspectionIssueSerializer(serializers.ModelSerializer):
    """An entry in the cover_page issue list."""

    class Meta:
        model = InspectionIssue
        fields = ['id', 'seq', 'description', 'status', 'photo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class InspectionDeviceSerializer(serializers.ModelSerializer):
    """A device line with expected values + onsite-collected readings."""

    asset_number = serializers.CharField(source='asset.asset_number', read_only=True)
    collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
    photos = InspectionPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = InspectionDevice
        fields = [
            'id', 'client_device_uid', 'row_order', 'asset', 'asset_number',
            'asset_id_text', 'category', 'brand_model', 'sn', 'usage', 'warranty_start',
            'photo_required', 'outline', 'device_notes',
            'status', 'ip_address', 'cpu', 'memory', 'hdd', 'windows_version',
            'ios_version', 'drive_c_free_space', 'intact_asset_tag', 'comment',
            'is_new_device', 'collected_by', 'collected_by_name', 'collected_at',
            'photos', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'asset_number', 'collected_by', 'collected_at',
            'created_at', 'updated_at',
        ]


class InspectionDeviceCacheSerializer(serializers.ModelSerializer):
    """Lightweight device payload for the offline cache download."""

    class Meta:
        model = InspectionDevice
        fields = [
            'id', 'client_device_uid', 'row_order', 'asset_id_text', 'category',
            'brand_model', 'sn', 'usage', 'warranty_start', 'photo_required',
            'outline', 'device_notes', 'status', 'is_new_device',
        ]


class StoreInspectionSerializer(serializers.ModelSerializer):
    """Store inspection header + progress + generated deliverables."""

    engineer_name = serializers.CharField(source='engineer.get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    device_total = serializers.SerializerMethodField()
    device_collected = serializers.SerializerMethodField()

    class Meta:
        model = StoreInspection
        fields = [
            'id', 'company', 'company_name', 'division', 'division_name',
            'location', 'location_name', 'jda_code', 'brand_name', 'store_name',
            'store_label', 'inspection_date', 'engineer', 'engineer_name', 'status',
            'status_display', 'arriving_time', 'leaving_time', 'wifi_coverage',
            'wifi_covers_store', 'it_support_rating', 'it_support_comment',
            'error_setting_fixed_count', 'store_issue_found_count', 'issue_to_follow_count',
            'device_counts', 'cover_extras', 'notes',
            'store_signature', 'engineer_signature', 'signed_at',
            'report_file', 'photo_zip', 'report_generated_at',
            'completion_percentage', 'device_total', 'device_collected',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'store_signature', 'engineer_signature', 'signed_at',
            'report_file', 'photo_zip', 'report_generated_at',
            'created_at', 'updated_at',
        ]

    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()

    def get_device_total(self, obj):
        return obj.devices.count()

    def get_device_collected(self, obj):
        return obj.devices.filter(collected_at__isnull=False).count()


class StoreInspectionDetailSerializer(StoreInspectionSerializer):
    """Detail view embeds devices and issues for one-shot offline download."""

    devices = InspectionDeviceCacheSerializer(many=True, read_only=True)
    issues = InspectionIssueSerializer(many=True, read_only=True)

    class Meta(StoreInspectionSerializer.Meta):
        fields = StoreInspectionSerializer.Meta.fields + ['devices', 'issues']
