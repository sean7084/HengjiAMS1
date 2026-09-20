"""
Kering-specific constants for the store device-inspection workflow.

These mirror the contracts enforced by the legacy EUS_Device_Inspec scripts
(`FeishuDeviceInspecAutomation.py` and `kering_inspection_folder_and_report_creation.py`)
so the mini program + report generator produce the same deliverable:
`<JDA> <Brand> <Store> Report Per Store.xlsx` (inspection_items, confirmation_page,
cover_page, asset_list) plus a Photo/ folder with the established naming convention.

Single source of truth shared by the REST API (checklist endpoint), the import
command (device-category normalization) and the report generator (labels/counts).
"""
from django.utils.translation import gettext_lazy as _

# ---------------------------------------------------------------------------
# Device-category normalization (ported from EUS DEVICE_CATEGORY_REPLACEMENTS)
# ---------------------------------------------------------------------------
# Legacy labels are mapped to canonical categories case-insensitively at import
# time, at collection time and again at report time so all stages agree.
DEVICE_CATEGORY_REPLACEMENTS = {
    'iphone': 'IOS_Device',
    'iphone se': 'IOS_Device',
    'iphonese': 'IOS_Device',
    'ipad': 'IOS_Device',
    'ipod': 'IOS_Device',
    'rfid': 'AR_Device',
    'rfid 8500': 'AR_Device',
    'lineapro': 'AR_Device',
    'linea pro': 'AR_Device',
    'ups': 'Other',
}


def normalize_device_category(value):
    """Map a legacy device-type label to its canonical category.

    Returns the original (stripped) text when there is no mapping, and preserves
    blank/None values so callers can distinguish "empty" from "unknown".
    """
    if value is None:
        return value
    text = str(value).strip()
    if not text:
        return text
    return DEVICE_CATEGORY_REPLACEMENTS.get(text.casefold(), text)


# ---------------------------------------------------------------------------
# Placeholder handling (ported from EUS ASSET_PLACEHOLDERS)
# ---------------------------------------------------------------------------
# Values that mean "no real identifier" and must be cleared / assigned a stable
# placeholder id so uniqueness and photo matching behave.
ASSET_PLACEHOLDERS = {
    '-', '--', 'n', 'na', 'n/a', 'nn', 'null', 'none', 'nil', '/',
    '无', '暂无', 'tbd', 'unknown',
}
ASSET_PLACEHOLDER_PREFIX = 'placeholder'

# Photo requirement tags used in the master asset list (照片需求 column).
PHOTO_REQUIRED_TAG = '需要拍照'
PHOTO_NOT_REQUIRED_TAG = '无需拍照'


def is_placeholder_identifier(value):
    """Return whether an SN / Asset-ID cell should be treated as blank."""
    if value is None:
        return True
    normalized = ' '.join(str(value).strip().split()).casefold()
    return normalized == '' or normalized in ASSET_PLACEHOLDERS


# ---------------------------------------------------------------------------
# Kering inspection checklist (inspection_items sheet)
# ---------------------------------------------------------------------------
# Faithful encoding of the "检查清单" sheet. Drives both the mini program's
# per-category capture guidance and the static inspection_items report sheet.
KERING_CHECKLIST = [
    {
        'section': '硬件类',
        'section_en': 'Hardware',
        'items': [
            {'no': 1, 'name': '电脑（笔记本/台式机）', 'name_en': 'Computer (Laptop/Desktop)', 'requirements': [
                '设备全貌照片（文件命名：产品类别+产品序列号）',
                '产品序列号照片',
                '电脑硬件信息(CPU，内存，硬盘）',
                '系统版本',
                'IP地址检查',
                'C盘可用空间检查',
            ]},
            {'no': 3, 'name': '显示器', 'name_en': 'Monitor', 'requirements': [
                '设备全貌照片', '产品序列号照片', '显示器尺寸',
            ]},
            {'no': 4, 'name': '彩色A4一体机', 'name_en': 'Color A4 MFP', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 5, 'name': '黑白A4打印机', 'name_en': 'B/W A4 Printer', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 6, 'name': '销售小票打印机 - TM88', 'name_en': 'Receipt Printer - TM88', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 7, 'name': '条码打印机- ZEBRA', 'name_en': 'Barcode Printer - ZEBRA', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 8, 'name': '收银钱箱', 'name_en': 'Cash Drawer', 'requirements': [
                '设备全貌照片', '连接模式',
            ]},
            {'no': 9, 'name': 'Xstore 商品扫码枪 - Symbol LS2208', 'name_en': 'Xstore Scanner - Symbol LS2208', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 10, 'name': 'Xstore 商品扫码枪 - Zebra DS2208', 'name_en': 'Xstore Scanner - Zebra DS2208', 'requirements': [
                '设备全貌照片', '产品序列号照片',
            ]},
            {'no': 11, 'name': 'iPad', 'name_en': 'iPad', 'requirements': [
                '系统信息照片（设置 - 关于本机 ）', '型号检查', 'iCloud检查', '电池检查', 'iOS系统更新',
            ]},
            {'no': 12, 'name': 'iPhone SE (扫枪用，音乐播放器用)', 'name_en': 'iPhone SE', 'requirements': [
                '系统信息照片（设置 - 关于本机 ）', '型号检查', 'iCloud检查', '电池检查', 'iOS系统更新',
            ]},
            {'no': 13, 'name': '扫枪外壳Linea Pro及充电底座', 'name_en': 'Linea Pro + Charger', 'requirements': [
                '数量', '设备全貌照片', '设备序列号',
            ]},
            {'no': 14, 'name': '扫描枪RFD8500及充电底座', 'name_en': 'RFD8500 + Charger', 'requirements': [
                '数量', '设备全貌照片', '设备序列号',
            ]},
            {'no': 15, 'name': 'RFD40 Premium Plus', 'name_en': 'RFD40 Premium Plus', 'requirements': [
                '数量', '设备全貌照片', '设备序列号',
            ]},
            {'no': 16, 'name': '机柜', 'name_en': 'IT Rack', 'requirements': [
                '设备全貌和细节照片', '清理机柜（正面）', '机柜尺寸',
            ]},
            {'no': 17, 'name': '配线架', 'name_en': 'Patch Panel', 'requirements': [
                '设备全貌照片',
            ]},
            {'no': 18, 'name': '路由器', 'name_en': 'Router', 'requirements': [
                '设备正面全貌照片', '清理路由器正面',
            ]},
            {'no': 19, 'name': '交换机', 'name_en': 'Switch', 'requirements': [
                '设备全貌照片', '清理交换机正面',
            ]},
        ],
    },
    {
        'section': '软件类',
        'section_en': 'Software',
        'items': [
            {'no': 20, 'name': '客流统计', 'name_en': 'ShopperTrak', 'requirements': ['口头确认，是否正常可用']},
            {'no': 21, 'name': 'Xstore', 'name_en': 'Xstore', 'requirements': ['口头确认，是否正常可用']},
            {'no': 22, 'name': 'JDA', 'name_en': 'JDA', 'requirements': ['口头确认，是否正常可用']},
            {'no': 23, 'name': 'Store BO', 'name_en': 'Store BO', 'requirements': ['口头确认，是否正常可用']},
            {'no': 24, 'name': 'Luce', 'name_en': 'Luce', 'requirements': ['口头确认，是否正常可用']},
            {'no': 25, 'name': 'Kering Service', 'name_en': 'Kering Service', 'requirements': ['口头确认，是否正常可用']},
            {'no': 26, 'name': '网速测试', 'name_en': 'Speed Test', 'requirements': ['有线和无线网络speed test照片']},
        ],
    },
]

# Per-category capture guidance for the mini program device-verify form.
# Each entry lists which structured readings and photos are relevant.
CATEGORY_CAPTURE_FIELDS = {
    'Desktop': ['ip_address', 'cpu', 'memory', 'hdd', 'windows_version', 'drive_c_free_space', 'intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'Laptop': ['ip_address', 'cpu', 'memory', 'hdd', 'windows_version', 'drive_c_free_space', 'intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'Monitor': ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'Printer': ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'Scanner': ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'IOS_Device': ['ios_version', 'is_company_phone', 'user_email', 'intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'AR_Device': ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo'],
    'Other': ['intact_asset_tag', 'comment', 'overall_photo'],
}
DEFAULT_CAPTURE_FIELDS = ['intact_asset_tag', 'comment', 'overall_photo', 'serial_photo']


def capture_fields_for_category(category):
    """Return the capture-field list for a (normalized) device category."""
    normalized = normalize_device_category(category) or ''
    return CATEGORY_CAPTURE_FIELDS.get(normalized, DEFAULT_CAPTURE_FIELDS)


# ---------------------------------------------------------------------------
# Structured picker options + required readings (blind-count field capture)
# ---------------------------------------------------------------------------
# Dropdown option lists for PC readings so audits stay consistent; the client
# also offers an "Other" free-text escape hatch for out-of-list hardware.
CPU_OPTIONS = ['Intel Ultra 5', 'Intel i5', 'AMD 6650U', 'AMD 5650U', 'AMD 4650U', 'AMD 3500U']
MEMORY_OPTIONS = ['32 GB', '16 GB', '8 GB', '4 GB']
HDD_OPTIONS = ['512 GB', '256 GB', '128 GB', '1T']
WINDOWS_OPTIONS = [
    'Windows 11 专业版', 'Windows 10 专业版', 'Windows 7 专业版', 'Windows 7 家庭版',
]

# Fields rendered as dropdowns on the device form.
FIELD_OPTIONS = {
    'cpu': CPU_OPTIONS,
    'memory': MEMORY_OPTIONS,
    'hdd': HDD_OPTIONS,
    'windows_version': WINDOWS_OPTIONS,
}

# Readings that must be filled before a device can be saved, per category.
# (Company-phone user_email is required conditionally when is_company_phone.)
CATEGORY_REQUIRED_FIELDS = {
    'Desktop': ['ip_address', 'cpu', 'memory', 'hdd', 'windows_version', 'drive_c_free_space'],
    'Laptop': ['ip_address', 'cpu', 'memory', 'hdd', 'windows_version', 'drive_c_free_space'],
    'IOS_Device': ['ios_version'],
}
DEFAULT_REQUIRED_FIELDS = []


def required_fields_for_category(category):
    """Return the must-fill reading list for a (normalized) device category."""
    normalized = normalize_device_category(category) or ''
    return CATEGORY_REQUIRED_FIELDS.get(normalized, DEFAULT_REQUIRED_FIELDS)


# ---------------------------------------------------------------------------
# Report labels
# ---------------------------------------------------------------------------
# cover_page "IT Equipment information" device rows (summary counts, in order).
COVER_PAGE_DEVICE_LABELS = [
    'Xstore PC', 'None POS PC', 'Monitor', 'Reception Printer', 'Barcode Printer',
    'Xstore Scanner', 'Scanner', 'AIO Printer', 'Black/White', 'iPad（Total）',
    'iPhone se（total）', 'Linea Pro', 'Linea Pro Charger', 'RFID', 'RFID Charger',
    'UPS', 'Cashdrawer', 'Patch Panel', 'Router', 'Switch', 'AP',
]

# The subset computed by build_cover_page_summary_counts from in-store asset rows.
# Mirrors EUS COVER_PAGE_SUMMARY_LABELS exactly. Patch Panel / Router / Switch / AP
# are NOT device-derived - the EUS pipeline fills those from rack/network data, so
# they are populated separately (from rack/network photos) by the report generator.
COVER_PAGE_SUMMARY_LABELS = (
    'Xstore PC', 'None POS PC', 'Monitor', 'Reception Printer', 'Barcode Printer',
    'Xstore Scanner', 'Scanner', 'AIO Printer', 'Black/White', 'iPad（Total）',
    'iPhone se（total）', 'Linea Pro', 'Linea Pro Charger', 'RFID', 'RFID Charger',
    'UPS', 'Cashdrawer',
)

# Map rack/network photo kinds -> the cover_page label they populate.
NETWORK_PHOTO_COUNT_LABELS = {
    'router': 'Router',
    'switch': 'Switch',
    'patchpanel': 'Patch Panel',
}

# confirmation_page device-count rows (engineer-confirmed counts, in order).
CONFIRMATION_COUNT_LABELS = [
    '台式机数量 （包括税控机，请标注税控机数量）',
    '笔记本数量 （包括税控机，请标注税控机数量）',
    'iPad数量',
    'iPhone se数量',
    '销售小票打印机数量',
    '标签打印机数量',
    '黑白打印机数量',
    '彩色一体机数量',
    '其他打印机数量',
    'Xstore商品扫码枪数量 - Symbol LS2208',
    'Xstore商品扫码枪数量 - Zebra DS2208',
    'Linea Pro扫描枪数量',
    'Linea Pro充电底座数量 - 四联充',
    'Linea Pro充电底座数量 - 单充',
    'RFID 扫描枪数量',
    'RFID 扫描枪充电底座数量 - 四联充',
    'RFID 扫描枪充电底座数量 - 单充',
    'RFD40 Premium Plus数量',
    '钱箱数量',
    'UPS数量',
    '显示器数量',
]

# asset_list sheet column headers (final report contract).
ASSET_LIST_COLUMNS = [
    'STORE', 'JDA', 'Asset ID', 'Category', 'Brand-Model', 'SN', 'Warranty-start',
    'Usage', 'Status', 'Comment', 'IP Address', 'CPU', 'Memory', 'HDD',
    'Windows&IOS Version', 'Drive C Free Space', 'Intact Asset Tag',
]

# ---------------------------------------------------------------------------
# Photo naming (ported from EUS photo conventions)
# ---------------------------------------------------------------------------
# Rack / network / issue / cash-drawer photo kinds map to fixed business names.
PHOTO_KIND_PREFIX = {
    'rack1': 'Rack1',
    'rack2': 'Rack2',
    'rack3': 'Rack3',
    'router': 'Router',
    'switch': 'Switch',
    'patchpanel': 'PatchPanel',
    'speedtest_ethernet': 'SpeedtestEthernet',
    'speedtest_wifi': 'SpeedtestWiFi',
    'issue': 'Issue',
    'cash_drawer': 'Other_Cash_Drawer',
}

# Recognized image extensions for photo handling / cleanup.
PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.heic', '.tiff', '.tif', '.webp'}

# Junk files removed from the Photo/ folder during report packaging.
PHOTO_JUNK_NAMES = {'thumbs.db', 'desktop.ini', '.ds_store'}

# Status values used on the asset_list sheet.
STATUS_IN_STORE = 'In Store'
STATUS_NOT_IN_STORE = 'Not In Store'
