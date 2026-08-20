# API Documentation - HengJi AMS

Base URL: `http://127.0.0.1:8000` (Development)  
Production: Replace with production domain

---

## Table of Contents

- [Authentication](#authentication)
- [Assets API](#assets-api)
- [Companies API](#companies-api)
- [Products API](#products-api)
- [Quotations API](#quotations-api)
- [Deliveries API](#deliveries-api)
- [Invoices API](#invoices-api)
- [Reports API](#reports-api)
- [Error Handling](#error-handling)

---

## Authentication

### Format

All API endpoints require authentication via **Session Cookie** or **Bearer Token**.

```http
Authorization: Bearer <token>
Cookie: sessionid=<session_id>
```

### Endpoints

#### POST /api/auth/login/

Authenticate user and receive access token.

**Request Body:**
```json
{
  "username": "admin",
  "password": "hjadmpass"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid-string",
    "username": "admin",
    "email": "admin@hengji.com",
    "roles": ["superadmin"],
    "is_active": true
  }
}
```

#### POST /api/auth/logout/

Invalidate current session/token.

#### GET /api/auth/user/

Get current authenticated user details.

**Response (200 OK):**
```json
{
  "id": "uuid-string",
  "username": "admin",
  "email": "admin@hengji.com",
  "first_name": "",
  "last_name": "",
  "roles": ["superadmin"],
  "has_perm": {
    "asset_management": true,
    "order_management": false
  }
}
```

---

## Assets API

### GET /api/assets/

List all accessible assets (paginated, 50 per page).

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `status` (str): Filter by status (`available`, `assigned`, `maintenance`)
- `category` (str): Filter by category UUID
- `brand` (str): Filter by brand UUID
- `search` (str): Search by serial_number or name
- `from_date` (date): Created after date
- `to_date` (date): Created before date

**Response (200 OK):**
```json
{
  "count": 1234,
  "next": "http://.../assets/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "asset_number": "KCNLP-001",
      "serial_number": "SN123456",
      "barcode": "1234567890",
      "status": "available",
      "condition": "good",
      "created_at": "2025-07-10T08:00:00Z",
      "updated_at": "2026-04-15T12:00:00Z"
    }
  ]
}
```

### GET /api/assets/{uuid}/

Retrieve specific asset details including nested objects.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "asset_number": "KCNLP-001",
  "serial_number": "SN123456",
  "barcode": "1234567890",
  "category": {
    "name": "Laptop",
    "item_type": "hardware"
  },
  "brand": {
    "name": "Dell",
    "logo": "https://.../dell-logo.png"
  },
  "model": {
    "name": "XPS 15",
    "model_number": "XP15-2025",
    "specifications": "Intel i7, 32GB RAM, 1TB SSD"
  },
  "status": "available",
  "location": {
    "name": "Shanghai Office",
    "zone": "Zone A",
    "rack": "Rack 5",
    "shelf": "S2"
  },
  "photo": "https://.../media/assets/photo.jpg",
  "assignment": {
    "assigned_to": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "assigned_at": "2026-04-01T10:00:00Z"
  }
}
```

### POST /api/assets/

Create new asset.

**Required Fields:**
- `category`: UUID string
- `brand`: UUID string
- `model`: UUID string
- `serial_number`: Optional

**Example Request:**
```json
{
  "category": "uuid-of-laptop-category",
  "brand": "uuid-of-dell-brand",
  "model": "uuid-of-xps-model",
  "serial_number": "SN987654",
  "barcode": "9876543210",
  "status": "available",
  "condition": "new",
  "location": "uuid-of-location",
  "quantity": 1,
  "zone": "Zone A",
  "rack": "Rack 3",
  "shelf": "S1"
}
```

### PUT /api/assets/{uuid}/

Update asset fields. Only provided fields are updated.

### DELETE /api/assets/{uuid}/

Delete asset (only available status allowed unless permission granted).

**Note**: Protected deletion prevents removal if assigned to active user or linked to maintenance records.

---

## Companies API

### GET /api/companies/

List companies accessible to authenticated user.

**Query Parameters:**
- `page` (int)
- `search` (str)
- `active` (bool)

### GET /api/companies/{uuid}/

Company details with divisions and locations.

**Response Structure:**
```json
{
  "id": "uuid",
  "name": "Tech Corp Ltd.",
  "code": "TECH",
  "type": "customer",
  "contact_person": "Jane Smith",
  "phone": "+86-21-1234-5678",
  "website": "https://techcorp.com",
  "address": "Shanghai Pudong New Area",
  "division_count": 5,
  "location_count": 12,
  "divisions": [/* array of division summaries */],
  "locations": [/* array of location summaries */]
}
```

### POST /api/companies/

Create new company record.

### GET /api/companies/{company_uuid}/locations/

List all locations under a company.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Main Warehouse",
    "code": "WH-SH-001",
    "chinese_name": "主仓库",
    "chinese_address": "上海市浦东新区张江镇",
    "zone_capacity": 100,
    "rack_count": 10,
    "shelf_per_rack": 5
  }
]
```

---

## Products API

### GET /api/products/

List all products (brands + models + prices).

**Query Parameters:**
- `page` (int)
- `category` (UUID)
- `brand` (UUID)
- `item_type` (str): `hardware` | `service`
- `search` (str)

### GET /api/product-prices/

Unified price list view (both hardware and services).

**Query Parameters:**
- `model` (UUID): Hardware model
- `service_item` (UUID): Service offering
- `is_current` (bool): Only return active/current prices
- `valid_from` (date)
- `valid_until` (date)

**Response:**
```json
{
  "count": 500,
  "results": [
    {
      "id": "uuid",
      "model": {
        "id": "uuid",
        "name": "MacBook Pro 16",
        "brand": "Apple"
      },
      "service_item": null,
      "unit": "each",
      "price_without_tax": 15000.00,
      "price_with_tax": 16950.00,
      "tax_rate": 13,
      "valid_from": "2026-01-01T00:00:00Z",
      "is_current": true
    }
  ]
}
```

### GET /api/services/

List service catalog items.

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "service_group": "IT Consulting",
      "name": "System Integration",
      "description": "Complete setup and configuration",
      "unit": "hours",
      "is_active": true
    }
  ]
}
```

---

## Quotations API

### GET /api/quotations/

List quotations with optional filters.

**Query Parameters:**
- `page` (int)
- `status` (str): `draft`, `sent`, `confirmed`, `cancelled`
- `customer` (UUID)
- `from_date` (date)
- `to_date` (date)
- `has_delivery` (bool)

### GET /api/quotations/{uuid}/

Full quotation details with line items and related documents.

**Response:**
```json
{
  "id": "uuid",
  "quotation_number": "QT-20260424-001",
  "customer": {
    "id": "uuid",
    "name": "Tech Corp Ltd.",
    "contact_person": "Mr. Wang"
  },
  "status": "sent",
  "attn": "Ms. Li",
  "attn_email": "li.m@techcorp.com",
  "total_without_tax": 150000.00,
  "total_with_tax": 169500.00,
  "notes": "Standard terms apply",
  "valid_until": "2026-05-24T00:00:00Z",
  "items": [
    {
      "id": "uuid",
      "product_description": "MacBook Pro 16-inch",
      "brand": "Apple",
      "unit": "each",
      "quantity": 10,
      "price_without_tax": 15000.00,
      "line_total": 150000.00
    }
  ],
  "related_purchase_order": null,
  "related_delivery": null,
  "pdf_url": "http://.../en-us/quotations/123/pdf/"
}
```

### POST /api/quotations/

Create new quotation draft.

### PUT /api/quotations/{uuid}/

Update quotation fields (draft state only).

### POST /api/quotations/{uuid}/pdf/

Generate and download PDF.

### POST /api/quotations/{uuid}/confirm/

Transition from `sent` → `confirmed`.

**After Confirmation:**
- Creates action button for "Create Purchase Order" or "Direct Dispatch"
- Adds quotation line items to purchase order upon creation

### POST /api/quotations/{uuid}/cancel/

Mark as cancelled (requires reason).

---

## Deliveries API

### GET /api/deliveries/

List delivery orders.

**Query Parameters:**
- `page` (int)
- `status` (str): `pending`, `dispatched`, `delivered`
- `quotation` (UUID)
- `from_date` (date)

### GET /api/deliveries/{uuid}/

Delivery details with line items and signature.

**Response:**
```json
{
  "id": "uuid",
  "delivery_number": "DO-20260425-001",
  "quotation": {
    "number": "QT-20260424-001"
  },
  "status": "pending",
  "receiver_name": "张先生",
  "receiver_phone": "+86-13800138000",
  "delivery_address": "上海市浦东新区世纪大道 1234 号",
  "delivery_method": "送货上门",
  "remarks": "Please call before delivery",
  "signed_file": null,
  "items": [
    {
      "id": "uuid",
      "asset": {
        "id": "uuid",
        "asset_number": "KCNLP-001",
        "serial_number": "SN123456"
      },
      "brand": "Apple",
      "product_description": "MacBook Pro 16-inch",
      "quantity": 1
    }
  ]
}
```

### POST /api/deliveries/

Create new delivery (usually triggered from confirmed quotation).

**Alternative via Quotation:**
```http
POST /api/quotations/{uuid}/create-delivery/
```

### POST /api/deliveries/{uuid}/dispatch/

Mark as dispatched and update asset statuses.

**Side Effects:**
- Asset status changes from `available` → `assigned`
- Creates `AssetAssignment` record

### POST /api/deliveries/{uuid}/mark-delivered/

Mark delivery completed and upload signed copy.

**Form Data Upload:**
```python
import requests

with open('signed_copy.pdf', 'rb') as f:
    response = requests.post(
        'http://127.0.0.1:8000/api/deliveries/uuid/mark-delivered/',
        files={'signed_file': f},
        data={'remarks': 'Signed by customer'}
    )
```

### POST /api/deliveries/{uuid}/pdf/

Generate delivery PDF document.

---

## Invoices API

### GET /api/invoices/weekly-batches/

List weekly invoice batches (SharePoint imports).

### POST /api/invoices/weekly-batches/

Upload weekly batch Excel file for processing.

**Multipart Form:**
```bash
curl -X POST \
  http://127.0.0.1:8000/api/invoices/weekly-batches/ \
  -F "sharepoint_file=@invoice-week-12.xlsx" \
  -H "Authorization: Bearer ..."
```

### GET /api/invoices/infos/

List invoice information records.

**Query Parameters:**
- `page` (int)
- `status` (str)
- `weekly_batch` (UUID)
- `quotation` (UUID)

### GET /api/invoices/infos/{uuid}/

Invoice details with line items.

### POST /api/invoices/infos/{uuid}/recalculate/

Recalculate amounts from source quotation/delivery.

### POST /api/invoices/infos/{uuid}/generate-document/

Generate invoice info sheet (Excel/PDF).

### GET /api/invoices/dispatches/

List email dispatches history.

### POST /api/invoices/dispatches/

Compose and send invoice email.

**Request Body:**
```json
{
  "invoice_info": "uuid-of-invoice",
  "to": ["client@example.com"],
  "cc": ["accounting@example.com"],
  "subject": "Invoice for Order QT-20260424-001",
  "body": "Dear Customer, please find attached your invoice.",
  "attachments": ["pdf_invoice_12345.pdf"]
}
```

### POST /api/invoices/dispatches/{uuid}/send/

Send draft email.

### POST /api/invoices/dispatches/{uuid}/forward-esker/

Forward to Esker system (internal process).

---

## Reports API

### GET /api/reports/charts/status-distribution/

Asset status distribution (pie chart).

**Response:**
```json
{
  "labels": ["Available", "Assigned", "Maintenance", "Disposed"],
  "data": [450, 620, 25, 15],
  "colors": ["green", "blue", "yellow", "gray"]
}
```

### GET /api/reports/charts/category-distribution/

Asset count by category.

### GET /api/reports/charts/brand-distribution/

Top brands visualization.

### GET /api/reports/charts/warranty-status/

Warranty expiration tracking.

### GET /api/reports/dashboard-config/

Retrieve dashboard chart preferences.

### POST /api/reports/dashboard-config/

Save dashboard configuration (charts to show/hide).

**Request Body:**
```json
{
  "show_warranty_chart": true,
  "chart_type_preference": "bar",
  "hide_charts": ["brand_distribution"]
}
```

### GET /api/reports/workflow-summary/

Workflow pipeline summary across all stages.

**Response:**
```json
{
  "quotation_pending": 15,
  "quotation_sent": 8,
  "purchase_purchasing": 5,
  "purchase_ordered": 12,
  "delivery_pending": 10,
  "delivery_dispatched": 3,
  "delivery_delivered": 7,
  "invoiced": 22
}
```

### GET /api/reports/export/assets.csv/

Export filtered assets to CSV.

**Query Parameters:** Same as `/api/assets/`

### GET /api/reports/export/assets.xlsx/

Export to Excel format.

### GET /api/reports/export/assets.pdf/

Export to PDF report.

---

## Error Handling

### Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Operation completed successfully |
| 201 | Created | Resource created (e.g., POST request) |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Conflicting operation (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Unexpected server exception |

### Error Response Format

All errors follow this standard structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "status",
        "errors": ["'invalid_status' is not a valid choice"]
      },
      {
        "field": "category",
        "errors": ["This field is required."]
      }
    ]
  }
}
```

### Common Error Codes

#### Authentication Errors
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Your session has expired. Please log in again."
  }
}
```

#### Validation Errors
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Cannot delete asset. It is currently assigned to a user.",
    "details": []
  }
}
```

#### Permission Errors
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You do not have permission to access this resource. Required role: order_management_procurement_specialist"
  }
}
```

#### Rate Limiting
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please retry after 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Testing the API

### Using curl

```bash
# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"hjadmpass"}'

# Get assets
curl http://127.0.0.1:8000/api/assets/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python Requests

```python
import requests

base_url = "http://127.0.0.1:8000"
auth_headers = {"Content-Type": "application/json"}

# Login
login_response = requests.post(
    f"{base_url}/api/auth/login/",
    json={"username": "admin", "password": "hjadmpass"},
    headers=auth_headers
)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Fetch assets
response = requests.get(f"{base_url}/api/assets/", headers=headers)
assets = response.json()

print(f"Found {assets['count']} assets")
```

### Django Test Client

For unit/integration testing within the project:

```python
from django.test import TestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AssetAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass')
        self.client.force_login(self.user)
    
    def test_list_assets(self):
        response = self.client.get('/api/assets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

---

*Last Updated: August 20, 2026*
