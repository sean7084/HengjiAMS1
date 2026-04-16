from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

import openpyxl
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from assets.models import AssetBrand, AssetCategory, AssetModel
from companies.models import Company, Division, Location
from customers.models import CustomerProfile
from deliveries.models import DeliveryOrder
from invoices.models import EmailDispatch, InvoiceInfo, WeeklyOrderBatch
from products.models import ProductPrice
from purchases.models import PurchaseOrder
from quotations.models import Quotation, QuotationItem


def _assert(name, condition):
    if not condition:
        raise AssertionError(f"FAIL: {name}")
    print(f"PASS: {name}")


def _mk_sharepoint_xlsx(po_number, internal_order, sap_cost_center):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Kering Group PO Number", "Internal Order", "SAP Cost Center"])
    ws.append([po_number, internal_order, sap_cost_center])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


def run():
    suffix = uuid4().hex[:8]
    today = date.today()

    user_model = get_user_model()
    user = user_model.objects.filter(is_superuser=True).first() or user_model.objects.first()
    _assert("user exists", user is not None)

    client = Client(HTTP_HOST="localhost")
    client.force_login(user)

    company = Company.objects.create(
        name=f"QIMS Smoke Co {suffix}",
        code=f"QIMS{suffix[:4].upper()}",
        status=Company.CompanyStatus.ACTIVE,
    )
    division = Division.objects.create(company=company, name=f"Division {suffix}", code=f"DIV{suffix[:3].upper()}")
    location = Location.objects.create(
        company=company,
        division=division,
        name=f"Warehouse {suffix}",
        code=f"LOC{suffix[:4].upper()}",
        status=Location.LocationStatus.ACTIVE,
        location_type=Location.LocationType.WAREHOUSE,
    )
    profile = CustomerProfile.objects.create(
        company=company,
        contact_person="Smoke Contact",
        phone="13800000000",
        email="smoke@example.com",
        delivery_address="Smoke Street 1",
        delivery_city="Shanghai",
        delivery_contact="Receiver Smoke",
        delivery_phone="13900000000",
        delivery_method=CustomerProfile.DeliveryMethod.DELIVERY,
        tax_id=f"TAX-{suffix}",
    )

    category = AssetCategory.objects.create(name=f"Category {suffix}", code=f"CAT{suffix[:6].upper()}")
    brand = AssetBrand.objects.create(name=f"Brand {suffix}", code=f"BR{suffix[:6].upper()}")
    model = AssetModel.objects.create(brand=brand, name=f"Model {suffix}", model_number=f"M-{suffix}")
    product_price = ProductPrice.objects.create(
        brand=brand,
        model=model,
        unit="PCS",
        price_without_tax=Decimal("100.00"),
        tax_rate=Decimal("13.00"),
        is_current=True,
    )

    quotation = Quotation.objects.create(
        customer=company,
        customer_profile=profile,
        quotation_date=today,
        valid_until=today + timedelta(days=15),
        attn=profile.contact_person,
        tel=profile.phone,
        status=Quotation.QuotationStatus.DRAFT,
    )
    q_item = QuotationItem.objects.create(
        quotation=quotation,
        product_price=product_price,
        quantity=1,
        user_brand="Kering",
        user_name="Store A",
    )
    quotation.refresh_from_db()
    _assert("quotation totals calculated", quotation.total_with_tax > 0)

    # Q2.4 path: quotation PDF generation
    pdf_resp = client.get(reverse("quotations:pdf", args=[quotation.pk]))
    _assert("quotation pdf endpoint responds", pdf_resp.status_code == 200)

    # confirm quotation
    confirm_resp = client.get(reverse("quotations:confirm", args=[quotation.pk]))
    _assert("quotation confirm redirect", confirm_resp.status_code == 302)
    quotation.refresh_from_db()
    _assert("quotation status confirmed", quotation.status == Quotation.QuotationStatus.CONFIRMED)

    # convert to purchase
    convert_resp = client.post(reverse("quotations:convert_to_purchase", args=[quotation.pk]))
    _assert("convert to purchase redirect", convert_resp.status_code == 302)
    purchase_order = PurchaseOrder.objects.get(quotation=quotation)
    _assert("purchase order created", purchase_order is not None)

    po_item = purchase_order.items.first()
    _assert("purchase order item exists", po_item is not None)

    # receive stock
    receive_payload = {
        "location": str(location.pk),
        "received_by": user.username or "smoke-user",
        "notes": "smoke receipt",
        f"qty_{po_item.pk}": "1",
        f"serials_{po_item.pk}": f"SN-{suffix}",
    }
    receive_resp = client.post(reverse("purchases:receive", args=[purchase_order.pk]), data=receive_payload)
    _assert("purchase receipt redirect", receive_resp.status_code == 302)
    purchase_order.refresh_from_db()
    _assert("purchase order complete", purchase_order.status == PurchaseOrder.Status.COMPLETE)

    # create delivery from quotation
    from assets.models import Asset

    available_assets = Asset.objects.filter(source_quotation=quotation, status=Asset.AssetStatus.AVAILABLE)
    asset = available_assets.first()
    _assert("received asset available", asset is not None)

    delivery_payload = {
        "delivery_date": str(today),
        "receiver_name": profile.delivery_contact,
        "receiver_phone": profile.delivery_phone,
        "delivery_address": f"{profile.delivery_address} {profile.delivery_city}",
        "delivery_method": profile.get_delivery_method_display(),
        "remarks": "smoke delivery",
        "selected_assets": [str(asset.pk)],
    }
    delivery_create_resp = client.post(reverse("deliveries:create_from_quotation", args=[quotation.pk]), data=delivery_payload)
    _assert("delivery create redirect", delivery_create_resp.status_code == 302)

    delivery = DeliveryOrder.objects.filter(quotation=quotation).order_by("-created_at").first()
    _assert("delivery created", delivery is not None)

    dispatch_resp = client.post(reverse("deliveries:dispatch", args=[delivery.pk]))
    _assert("delivery dispatch redirect", dispatch_resp.status_code == 302)
    delivery.refresh_from_db()
    _assert("delivery dispatched", delivery.status == DeliveryOrder.Status.DISPATCHED)

    upload_resp = client.post(
        reverse("deliveries:upload_signed", args=[delivery.pk]),
        data={"signed_file": SimpleUploadedFile("signed.pdf", b"%PDF-1.4 smoke", content_type="application/pdf")},
    )
    _assert("signed upload redirect", upload_resp.status_code == 302)

    complete_resp = client.post(reverse("deliveries:complete", args=[delivery.pk]))
    _assert("delivery complete redirect", complete_resp.status_code == 302)
    delivery.refresh_from_db()
    _assert("delivery completed", delivery.status == DeliveryOrder.Status.COMPLETED)

    # invoice batch import via view
    po_number = f"PO-{suffix}"
    io_number = f"IO-{suffix}"
    sap_number = f"SAP-{suffix}"
    xlsx_bytes = _mk_sharepoint_xlsx(po_number, io_number, sap_number)
    import_resp = client.post(
        reverse("invoices:batch_import"),
        data={
            "sharepoint_file": SimpleUploadedFile(
                f"sharepoint_{suffix}.xlsx",
                xlsx_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    _assert("invoice batch import redirect", import_resp.status_code == 302)

    batch = WeeklyOrderBatch.objects.order_by("-uploaded_at").first()
    _assert("weekly batch processed", batch and batch.status == WeeklyOrderBatch.Status.PROCESSED)

    invoice = InvoiceInfo.objects.filter(weekly_batch=batch).first()
    _assert("invoice info created", invoice is not None)

    # link invoice to quotation + delivery and recalc
    update_payload = {
        "invoice_date": str(invoice.invoice_date),
        "payment_due_date": str(today + timedelta(days=30)),
        "bill_to": company.name,
        "kering_group_po_number": invoice.kering_group_po_number,
        "internal_order": invoice.internal_order,
        "sap_cost_center": invoice.sap_cost_center,
        "quotation": str(quotation.pk),
        "delivery_order": str(delivery.pk),
    }
    update_resp = client.post(reverse("invoices:invoice_update", args=[invoice.pk]), data=update_payload)
    _assert("invoice update redirect", update_resp.status_code == 302)

    recalc_resp = client.post(reverse("invoices:invoice_recalculate", args=[invoice.pk]))
    _assert("invoice recalc redirect", recalc_resp.status_code == 302)
    invoice.refresh_from_db()
    _assert("invoice gross amount calculated", invoice.gross_amount > 0)

    invoice_doc_resp = client.get(reverse("invoices:invoice_document", args=[invoice.pk]))
    _assert("invoice document endpoint responds", invoice_doc_resp.status_code == 200)

    # dispatch transition
    preview_resp = client.post(
        reverse("invoices:email_dispatch_compose_from_quotation", args=[quotation.pk]),
        data={
            "quotation": str(quotation.pk),
            "delivery_order": str(delivery.pk),
            "invoice_info": str(invoice.pk),
            "sent_to": "client@example.com",
            "cc": "",
            "bcc": "",
            "subject": f"Smoke Dispatch {suffix}",
            "body": "Smoke dispatch preview",
            "action": "preview",
        },
    )
    _assert("email compose preview responds", preview_resp.status_code == 200)

    dispatch = EmailDispatch.objects.create(
        quotation=quotation,
        delivery_order=delivery,
        invoice_info=invoice,
        sent_to="client@example.com",
        subject=f"Smoke Dispatch Transition {suffix}",
        body="Smoke body",
        status=EmailDispatch.DispatchStatus.SENT,
        created_by=user,
    )

    client_confirm_resp = client.post(reverse("invoices:email_dispatch_client_confirmed", args=[dispatch.pk]))
    _assert("dispatch client confirm redirect", client_confirm_resp.status_code == 302)
    dispatch.refresh_from_db()
    _assert("dispatch status client confirmed", dispatch.status == EmailDispatch.DispatchStatus.CLIENT_CONFIRMED)

    esker_resp = client.post(reverse("invoices:email_dispatch_esker_forward", args=[dispatch.pk]))
    _assert("dispatch esker forward redirect", esker_resp.status_code == 302)
    dispatch.refresh_from_db()
    _assert("dispatch status esker forwarded", dispatch.status == EmailDispatch.DispatchStatus.ESKER_FORWARDED)

    # workflow pages
    wf_dashboard = client.get(reverse("dashboard:workflow_dashboard"))
    wf_search = client.get(reverse("dashboard:workflow_search"), {"q": quotation.quotation_number})
    _assert("workflow dashboard 200", wf_dashboard.status_code == 200)
    _assert("workflow search 200", wf_search.status_code == 200)

    print("\nSMOKE SUMMARY: PASS - quotation -> purchase -> delivery -> invoice -> dispatch transitions verified.")


run()
