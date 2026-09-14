"""
Photo naming rules for the store-inspection deliverable.

Ported from the EUS Feishu automation conventions:
- Device overall photo  -> `<Category><SN>-1.<ext>`
- Device serial photo   -> `<Category><SN>-2.<ext>`
- Extra device photos   -> `<Category><SN>-N.<ext>` (N increments; notes: 多张照片加-序号)
- Cash drawer           -> `Other_Cash_Drawer N.<ext>`
- Rack / network / test -> `Rack1-1`, `Router-1`, `Switch-1`, `PatchPanel-1`,
                           `SpeedtestEthernet-1`, `SpeedtestWiFi-1`, `Issue-1`

`assign_photo_display_names` is the single place that computes the business-facing
filename for every photo on an inspection, so the report workbook, the Photo zip and
any parity test all agree.
"""
import os

from inspections.constants import PHOTO_KIND_PREFIX, normalize_device_category
from inspections.models import InspectionPhoto

# Overall photo first, then serial, then any extras - matches the -1/-2 convention.
_DEVICE_KIND_ORDER = {
    InspectionPhoto.Kind.OVERALL: 0,
    InspectionPhoto.Kind.SERIAL: 1,
}


def _extension(image_field):
    """Return the lowercase file extension (with dot) for a photo's image."""
    name = getattr(image_field, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    return ext or '.jpg'


def _sanitize_sn(sn):
    """Compact a serial number for use inside a filename."""
    return ''.join(str(sn or '').split()) or 'NA'


def device_photo_name(category, sn, index, ext):
    """`<NormalizedCategory><SN>-<index><ext>`."""
    cat = normalize_device_category(category) or ''
    return f'{cat}{_sanitize_sn(sn)}-{index}{ext}'


def kind_photo_name(kind, index, ext):
    """Name for rack/network/issue/cash-drawer photos (no owning device)."""
    prefix = PHOTO_KIND_PREFIX.get(kind)
    if prefix is None:
        return f'{kind}-{index}{ext}'
    if kind == InspectionPhoto.Kind.CASH_DRAWER:
        return f'{prefix} {index}{ext}'
    return f'{prefix}-{index}{ext}'


def assign_photo_display_names(inspection):
    """Compute and persist `display_name` for every photo on an inspection.

    Returns the list of photos (with display_name set). Deterministic ordering keeps
    re-generation stable: device photos by (kind, sort_index, created_at); standalone
    photos by (kind, sort_index, created_at) with a per-kind counter.
    """
    photos = list(
        inspection.photos.select_related('device').order_by('sort_index', 'created_at')
    )

    # Device-attached photos: sequential index per device (overall=-1, serial=-2, ...).
    device_counters = {}
    # Standalone photos: sequential index per kind.
    kind_counters = {}

    for photo in photos:
        ext = _extension(photo.image)
        if photo.device_id is not None:
            device_key = photo.device_id
            index = device_counters.get(device_key, 0) + 1
            device_counters[device_key] = index
            photo.display_name = device_photo_name(
                photo.device.category, photo.device.sn, index, ext
            )
        else:
            kind = photo.kind
            index = kind_counters.get(kind, 0) + 1
            kind_counters[kind] = index
            photo.display_name = kind_photo_name(kind, index, ext)

    # Persist names in bulk (avoid N save() calls hitting auto_now side effects).
    InspectionPhoto.objects.bulk_update(photos, ['display_name'])
    return photos
