"""
Report-time transforms ported from the EUS Feishu automation.

These operate on the collected `InspectionDevice` rows for one inspection and
reproduce the business rules the legacy script applied before writing the report:
- cover_page summary counts (Category/Usage/Brand-Model -> label)
- XStore peripheral linking (attach host PC Asset ID to xstore-N peripherals)
- monitor size comment markers
- Intact Asset Tag autofill (N when blank or Asset ID missing)
- Windows/iOS version merge and In Store / Not In Store status

NOTE: The cover-page mapping and monitor-size table are Kering-specific heuristics.
They are centralized here so they can be validated/tuned against the golden
`22149 Gucci SZOL` output (see the report parity test).
"""
import re

from inspections.constants import COVER_PAGE_SUMMARY_LABELS, STATUS_IN_STORE, STATUS_NOT_IN_STORE

# Monitor model -> screen size (inches), ported verbatim from the EUS automation
# (MONITOR_MODEL_SIZES). Keys are normalize_monitor_model_key(brand_model).
MONITOR_MODEL_SIZES = {
    'lenovot1714': 17, 'lenovot1714a': 17, 'lenovol1710': 17, 'lenovol1714': 17,
    'lenovol1713a': 17, 'lenovod17195he0': 17, 'lenovoh17195hv0': 17,
    'lenovoa17195he0': 17, 'lenovol1795heo': 17, 'delle1715s': 17, 'delle177fpc': 17,
    'delle190sf': 19, 'lenovol1920': 19, 'tsinghuatongfangtdy19e82kg': 19,
    'lenovote2010': 19.5, 'lenovote201019.5': 19.5, 'lenovote2011': 19.5, 'lenovote2014': 19.5,
    'lenovot2054f': 20, 'le20gmkav': 20,
    'lenovov2225s': 21.5, 'lenovoa21238ft0': 21.5, 'lenovols222f': 22, 'ls2224a': 22,
    'lenovot24t': 24, 'lenovot24t20': 24, 'thinakvisiont24t': 24,
    'philips271v8': 27, 'samsungqm55r': 55, 'qm65r': 65,
}
MONITOR_SIZE_MARKER_PATTERN = re.compile(r'\d+(?:\.\d+)?-in\b', re.IGNORECASE)

# Usage tokens that identify a peripheral bound to an XStore host (xstore-1..4).
_XSTORE_PERIPHERAL_RE = re.compile(r'^xstore-\d+$', re.IGNORECASE)


def normalize_monitor_model_key(value):
    """Normalize a monitor brand-model to a lookup key for the size table."""
    normalized = _text(value)
    if not normalized:
        return ''
    return re.sub(r'[^a-z0-9.]+', '', normalized.casefold())


def format_monitor_size_marker(size):
    """Format a monitor size as its comment marker, e.g. 19.5 -> '19.5-in'."""
    if float(size).is_integer():
        return f'{int(size)}-in'
    return f'{size}-in'


def _text(value):
    return (value or '').strip()


def _lower(value):
    return _text(value).casefold()


def merged_version(device):
    """Merge Windows and iOS versions into the single asset_list column value."""
    parts = [p for p in (_text(device.windows_version), _text(device.ios_version)) if p]
    return ' / '.join(parts)


def effective_status(device):
    """In Store when verified onsite, otherwise Not In Store.

    The API stamps `collected_at` on every device the engineer touches, so an
    expected device that was never collected is reported as Not In Store (missing),
    while an explicitly added new device is In Store.
    """
    if device.status == 'not_in_store':
        return STATUS_NOT_IN_STORE
    if device.collected_at is not None:
        return STATUS_IN_STORE
    return STATUS_IN_STORE if device.is_new_device else STATUS_NOT_IN_STORE


def autofill_intact_tag(device):
    """Return Y/N for the Intact Asset Tag, defaulting to N when unknown."""
    tag = _text(device.intact_asset_tag).upper()
    if tag in ('Y', 'N'):
        return tag
    if not _text(device.asset_id_text):
        return 'N'
    return tag or 'N'


def apply_monitor_size_comment(device):
    """Append the model's size marker to a monitor comment (EUS port).

    Strips any existing '<n>-in' marker before re-appending the correct one, so
    regenerating a report keeps the comment idempotent.
    """
    if _lower(device.category) != 'monitor':
        return device.comment
    size = MONITOR_MODEL_SIZES.get(normalize_monitor_model_key(device.brand_model))
    if size is None:
        return device.comment
    marker = format_monitor_size_marker(size)
    current = device.comment
    if current is None or _text(current) == '':
        return marker
    parts = [part.strip() for part in MONITOR_SIZE_MARKER_PATTERN.sub('', current).split(';')]
    parts = [part for part in parts if part]
    parts.append(marker)
    return '; '.join(parts)


def apply_new_device_marker(device, comment):
    """Mark onsite-new devices with a 'NEW' comment token (EUS behavior).

    New devices discovered during the visit (not in the master asset list) are
    flagged so the report reader can spot additions. Any existing comment text is
    preserved; the marker is appended once.
    """
    text = _text(comment)
    if not getattr(device, 'is_new_device', False):
        return text
    parts = [part.strip() for part in text.split(';')] if text else []
    if 'NEW' in parts:
        return text
    parts.append('NEW')
    return '; '.join(part for part in parts if part)


def link_xstore_peripherals(devices):
    """Attach the primary XStore host PC's Asset ID to xstore-N peripherals.

    Two-pass port: (1) find the primary XStore PC (Desktop preferred over Laptop);
    (2) for peripherals whose Usage matches xstore-N, append `PC: <Asset ID>`.
    Mutates and returns the same device list.
    """
    host_asset_id = ''
    desktop_host = None
    laptop_host = None
    for device in devices:
        if _lower(device.category) in ('desktop', 'laptop') and _lower(device.usage) == 'xstore':
            if _lower(device.category) == 'desktop' and desktop_host is None:
                desktop_host = device
            elif _lower(device.category) == 'laptop' and laptop_host is None:
                laptop_host = device
    host = desktop_host or laptop_host
    if host is not None:
        host_asset_id = _text(host.asset_id_text)

    if host_asset_id:
        for device in devices:
            if _lower(device.category) in ('scanner', 'printer') and _XSTORE_PERIPHERAL_RE.match(_text(device.usage)):
                marker = f'PC: {host_asset_id}'
                comment = _text(device.comment)
                if marker not in comment:
                    device.comment = f'{comment}; {marker}' if comment else marker
    return devices


def build_cover_page_summary_counts(devices):
    """Exact port of the EUS `build_cover_page_summary_counts`.

    Counts in-store devices onto the 17 COVER_PAGE_SUMMARY_LABELS using the EUS
    rules: independent checks (a row may increment more than one label); PCs and
    printers/scanners keyed by Category+Usage; iPad/iPhone/RFID/Linea keyed by
    Brand-Model substrings. Patch Panel / Router / Switch / AP are NOT device
    counts - the report generator fills those from rack/network photos.
    """
    counts = {label: 0 for label in COVER_PAGE_SUMMARY_LABELS}
    for device in devices:
        if effective_status(device) != STATUS_IN_STORE:
            continue
        category = _lower(device.category)
        usage = _lower(device.usage)
        brand_model = _lower(device.brand_model)

        is_pc = category in ('desktop', 'laptop')
        if is_pc and usage == 'xstore':
            counts['Xstore PC'] += 1
        elif is_pc:
            counts['None POS PC'] += 1

        if category == 'monitor':
            counts['Monitor'] += 1

        if category == 'printer' and 'tm-t88' in brand_model:
            counts['Reception Printer'] += 1
        if category == 'printer' and usage == 'label':
            counts['Barcode Printer'] += 1
        if category == 'scanner' and usage == 'xstore':
            counts['Xstore Scanner'] += 1
        elif category == 'scanner':
            counts['Scanner'] += 1
        if category == 'printer' and usage == 'aio':
            counts['AIO Printer'] += 1
        if category == 'printer' and usage == 'a4':
            counts['Black/White'] += 1

        if 'ipad' in brand_model or category == 'ipad':
            counts['iPad（Total）'] += 1
        if 'iphone se' in brand_model or category == 'iphonese':
            counts['iPhone se（total）'] += 1
        if 'linea' in brand_model and 'charger' not in brand_model:
            counts['Linea Pro'] += 1
        if 'linea pro charger' in brand_model or 'lineapro charger' in brand_model:
            counts['Linea Pro Charger'] += 1
        if 'rfid charger' in brand_model or 'crduniv' in brand_model:
            counts['RFID Charger'] += 1
        elif 'rfid' in brand_model and 'charger' not in brand_model:
            counts['RFID'] += 1

        if category == 'ups' or (
            category == 'other' and brand_model and 'ups' in brand_model and 'smc' in brand_model
        ):
            counts['UPS'] += 1
        if 'cash drawer' in brand_model or 'cashdrawer' in brand_model or '钱箱' in brand_model:
            counts['Cashdrawer'] += 1

    return counts
