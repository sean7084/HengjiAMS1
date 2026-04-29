"""Services for delivery template filling and PDF generation."""

from pathlib import Path
import shutil
import subprocess

from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string

from assets.models import Asset

from .models import DeliveryOrder

from openpyxl import load_workbook
from weasyprint import HTML


INTERNAL_WAREHOUSE_LOCATION_ID = 3


def get_dispatch_asset_queryset(quotation):
    if quotation is None:
        return Asset.objects.none()

    item_filters = Q()
    quotation_items = quotation.items.select_related('product_price__brand', 'product_price__model')
    for item in quotation_items:
        if not item.product_price_id or not item.product_price.brand_id or not item.product_price.model_id:
            continue
        item_filters |= Q(brand_id=item.product_price.brand_id, model_id=item.product_price.model_id)

    if not item_filters:
        return Asset.objects.none()

    active_delivery_statuses = [
        DeliveryOrder.Status.PENDING,
        DeliveryOrder.Status.PREPARED,
        DeliveryOrder.Status.DISPATCHED,
    ]

    return Asset.objects.filter(
        status=Asset.AssetStatus.AVAILABLE,
        location_id=INTERNAL_WAREHOUSE_LOCATION_ID,
    ).filter(
        item_filters,
    ).exclude(
        delivery_items__delivery_order__status__in=active_delivery_statuses,
    ).select_related('brand', 'model').distinct().order_by('asset_number')


def _find_label_cell(sheet, label):
    label = str(label).strip()
    for row in sheet.iter_rows():
        for cell in row:
            if str(cell.value).strip() == label:
                return cell
    return None


def _fill_by_label(sheet, label, value):
    cell = _find_label_cell(sheet, label)
    if not cell:
        return False

    target = sheet.cell(row=cell.row, column=cell.column + 1)
    target.value = value
    return True


def _find_item_header_map(sheet):
    expected = {
        '序列号': 'serial_number',
        '品牌': 'brand_name',
        '商品描述': 'product_description',
        '采购方品牌': 'user_brand',
        '采购方用户': 'user_name',
        '数量': 'quantity',
    }

    for row in sheet.iter_rows(min_row=1, max_row=150):
        header_map = {}
        for cell in row:
            text = str(cell.value).strip() if cell.value is not None else ''
            if text in expected:
                header_map[expected[text]] = cell.column

        if len(header_map) >= 3:
            return row[0].row, header_map

    return None, {}


def fill_delivery_template(delivery_order):
    """Fill delivery Excel template and return generated xlsx path."""
    template_path = Path(settings.BASE_DIR) / 'template_files' / '签收单 template.xlsx'
    if not template_path.exists():
        raise FileNotFoundError(f'Template not found: {template_path}')

    workbook = load_workbook(template_path)
    sheet = workbook.active

    _fill_by_label(sheet, '订货方', delivery_order.quotation.customer.name)
    _fill_by_label(sheet, '收货人', delivery_order.receiver_name)
    _fill_by_label(sheet, '电话', delivery_order.receiver_phone)
    _fill_by_label(sheet, '交货地址', delivery_order.delivery_address)
    _fill_by_label(sheet, '交货方式', delivery_order.delivery_method)

    # Try common date labels
    if not _fill_by_label(sheet, '日期', delivery_order.delivery_date.strftime('%Y-%m-%d')):
        _fill_by_label(sheet, '送货日期', delivery_order.delivery_date.strftime('%Y-%m-%d'))

    start_row, header_map = _find_item_header_map(sheet)
    if start_row and header_map:
        row_idx = start_row + 1
        for item in delivery_order.items.all().order_by('id'):
            values = {
                'serial_number': item.serial_number,
                'brand_name': item.brand_name,
                'product_description': item.product_description,
                'user_brand': item.user_brand,
                'user_name': item.user_name,
                'quantity': item.quantity,
            }
            for key, col in header_map.items():
                sheet.cell(row=row_idx, column=col).value = values.get(key, '')
            row_idx += 1

    output_dir = Path(settings.MEDIA_ROOT) / 'deliveries' / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = output_dir / f'{delivery_order.delivery_number}.xlsx'
    workbook.save(xlsx_path)

    return xlsx_path


def _find_soffice_binary():
    candidates = [
        shutil.which('soffice'),
        shutil.which('soffice.exe'),
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)

    return None


def convert_xlsx_to_pdf(xlsx_path):
    """Convert xlsx to pdf with LibreOffice headless. Returns pdf path or None."""
    soffice = _find_soffice_binary()
    if not soffice:
        return None

    xlsx_path = Path(xlsx_path)
    outdir = str(xlsx_path.parent)

    try:
        subprocess.run(
            [
                soffice,
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                outdir,
                str(xlsx_path),
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
    except Exception:
        return None

    pdf_path = xlsx_path.with_suffix('.pdf')
    return pdf_path if pdf_path.exists() else None


def render_delivery_pdf_html(delivery_order):
    """Render delivery order PDF bytes from Django HTML template (LibreOffice-free path)."""
    ordered_items = list(delivery_order.items.all().order_by('id'))
    display_rows = []
    for item in ordered_items:
        display_rows.append({
            'serial_number': item.serial_number,
            'brand_name': item.brand_name,
            'product_description': item.product_description,
            'user_brand': item.user_brand,
            'user_name': item.user_name,
            'quantity': item.quantity,
        })

    while len(display_rows) < 6:
        display_rows.append({
            'serial_number': '',
            'brand_name': '',
            'product_description': '',
            'user_brand': '',
            'user_name': '',
            'quantity': '',
        })

    delivery_method_display = (delivery_order.delivery_method or '').strip() or '-'

    context = {
        'delivery': delivery_order,
        'display_rows': display_rows,
        'delivery_method_display': delivery_method_display,
        'logo_path': (Path(settings.BASE_DIR) / 'static' / 'images' / 'quotation_template_logo.png').resolve().as_uri(),
        'acceptance_text': '订货方或收货人在本签收单或快递公司承运单上签收后，即视为对以上商品进行了签收。',
    }

    html = render_to_string('deliveries/pdf_excel_style.html', context)
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
