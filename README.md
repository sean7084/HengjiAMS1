# HengJi Asset Management System (AMS)

[![Django](https://img.shields.io/badge/Django-5.2.3-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

A comprehensive SaaS asset management solution built with Django, supporting multi-language (English/Chinese), 2FA authentication, and multi-company asset tracking.

![Logo](media/logo.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Progress](#project-progress)
- [TODO](#todo)
- [Quotation & Invoice Management System](#quotation--invoice-management-system)
- [Test Accounts](#test-accounts)
- [Documentation](#documentation)

---

## Overview

HengJi AMS is an enterprise asset management system designed for organizations to track, manage, and audit their physical assets across multiple companies and divisions.

### Key Capabilities

- Multi-company, multi-division asset management
- Role-based access control (Superadmin, IT Administrator, Viewer)
- 2FA authentication enforcement
- Asset lifecycle tracking (assignment, return, maintenance, disposal)
- Multi-language support (English / Simplified Chinese)
- Bulk import/export (CSV, Excel, PDF)
- Mobile-responsive design

---

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Asset Management** | Full CRUD operations, barcode support, photo uploads |
| **Assignment System** | Assign assets to users, locations, or departments |
| **Return Processing** | Track asset returns with condition assessment |
| **Maintenance Tracking** | Schedule and record maintenance activities |
| **Warranty Monitoring** | Automatic warranty status and expiration alerts |
| **Depreciation Calculation** | Built-in depreciation tracking per category |
| **Audit System** | Comprehensive change logging and audit trails |
| **Import/Export** | Bulk import via CSV/Excel, multi-format export |
| **Advanced Filtering** | Filter by status, category, brand, date, location |

### User Management

- Three-tier role system: Superadmin, IT Administrator, Viewer
- Company-division-location based access control
- 2FA enforcement for all users
- Profile management with avatar support

### Asset Numbering

Three asset numbering modes supported:

1. **Continuity**: Auto-incrementing (e.g., `KCNLP-1`, `KCNLP-2`)
2. **Prefix + SN**: Company code + Serial Number (e.g., `CNSP-{SERIAL}`)
3. **Custom**: Manual import from external systems (e.g., accounting)

### Internationalization

- English (`en`)
- Simplified Chinese (`zh-hans`)
- Language switch on login page and profile settings

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.2.3 |
| Database (Dev) | SQLite |
| Database (Prod) | PostgreSQL |
| Authentication | django-otp (2FA) |
| ORM | Django ORM |
| Frontend | Bootstrap 5, HTML5, CSS3, JavaScript |
| Excel Export | openpyxl |
| PDF Export | reportlab |
| Internationalization | Django i18n |

### Style Reference

UI design inspired by [Ralph](https://ralphapp.com/) and [Snipe-IT](https://snipeitapp.com/) with a lightweight aesthetic.

---

## Project Structure

```
HengjiAMS1/
├── accounts/              # User authentication, 2FA, user management
│   ├── models.py          # Custom User model with roles
│   ├── views.py           # Login, logout, profile views
│   └── forms.py           # Authentication forms
│
├── assets/                # Core asset management
│   ├── models.py          # Asset, Category, Brand, Model, Assignment
│   ├── views.py           # Asset CRUD, import/export, categories, brands
│   ├── forms.py           # Asset forms with validation
│   └── urls.py            # Asset URL routing
│
├── companies/             # Company structure management
│   ├── models.py          # Company, Division, Location, CompanyUser
│   ├── views.py           # Company management views
│   └── urls.py            # Company URL routing
│
├── audit/                 # Audit and tracking
│   └── models.py          # Audit log models
│
├── reports/               # Reporting and analytics
│   └── views.py           # Report generation views
│
├── dashboard/             # Main dashboard
│   └── views.py           # Dashboard view with statistics
│
├── hengjiams/             # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI application
│
├── templates/             # Global templates
│   ├── base/              # Base template with navigation
│   ├── accounts/          # Auth templates (login, etc.)
│   ├── assets/            # Asset templates
│   ├── companies/         # Company templates
│   └── dashboard/         # Dashboard templates
│
├── locale/                # Translation files
├── media/                 # User uploads
├── static/                # Static files (CSS, JS, images)
├── template_files/        # Excel templates for PDF generation
│   ├── quotation template.xlsx
│   ├── 签收单 template.xlsx
│   └── invoice information template.xlsx
├── docs/                  # Documentation and changelogs
├── manage.py              # Django management script
└── db.sqlite3             # Development database
```

### App Responsibilities

| App | Purpose |
|-----|---------|
| `accounts` | User authentication, 2FA, profile management, role management |
| `assets` | Asset CRUD, categories, brands, models, assignments, maintenance |
| `companies` | Company, Division, Location, Company-User associations |
| `audit` | System audit logging and compliance tracking |
| `reports` | Analytics and reporting views |
| `dashboard` | Main landing page with statistics |
| `products` | Product price list (extends AssetBrand/AssetModel) |
| `customers` | Customer profiles (extends Company) |
| `quotations` | Quotation creation, PDF generation, attachments |
| `deliveries` | Delivery order (签收单) generation and tracking |
| `invoices` | Invoice info sheets, weekly batch processing |
| `emails` | Email composition, dispatch, Esker forwarding |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Conda environment: `HengjiAMS1`
- Django 5.2.3

### 1. Activate Conda Environment

```bash
conda activate HengjiAMS1
```

### 2. Install Dependencies

```bash
pip install django==5.2.8 django-otp openpyxl reportlab django-extensions
```

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Start Development Server

```bash
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000/

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | Django settings module | `hengjiams.settings` |
| `SECRET_KEY` | Django secret key | (dev key in settings) |
| `DEBUG` | Debug mode | `True` |

### Database Configuration

**Development (SQLite):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Production (PostgreSQL):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hengjiams_db',
        'USER': 'hengjiamsdjango',
        'PASSWORD': 'hengjiams_djangopass',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}
```

### Language Settings

Supported languages are configured in `settings.py`:
```python
LANGUAGES = [
    ('en', 'English'),
    ('zh-hans', 'Simplified Chinese'),
]
```

To switch language, use the language selector on:
- Login page (below credentials)
- Profile settings page (bottom navigation)

### 2FA Setup

The system uses `django-otp` for two-factor authentication. Users are enforced to enable 2FA after login.

### Asset Numbering Prefix

Configure `asset_prefix` on each `Company` model to control asset number generation.

---

## Project Progress

### Version History

| Version | Date | Focus |
|---------|------|-------|
| v0.0.1 | July 2025 | Foundation - Django setup, auth, i18n framework |
| v0.0.2 | August 2025 | Major Features - Asset models, audit system, RBAC |
| v0.0.3 | August 2025 | Consolidation - Category/Brand management, export, UI fixes |
| v0.0.4 | April 2026 | 2FA, Reporting, Mobile API, REST API |
| v0.1.0 | April 2026 | Quotation & Invoice Management System |

### Current Status (v0.1.0)

#### Fully Operational Features

- User authentication with role-based permissions
- Dashboard with role-filtered statistics
- Company, Division & Location management
- Complete Asset CRUD operations
- Asset Assignment & Return with audit trails
- Audit system with comprehensive change tracking
- Multi-language support (EN/ZH)
- Admin panel with Django styling
- Data export (CSV, Excel, PDF)
- Mobile-responsive Bootstrap 5 design
- Asset list customization (column visibility, filtering)
- **2FA with TOTP** - Full setup and verification workflow
- **Advanced Reporting** - Charts and analytics dashboard with Chart.js
- **Enhanced Mobile Features** - Barcode scanning with Html5-QRCode
- **REST API** - Full API endpoints at /api/v1/ with documentation at /docs/
- **Quotation & Invoice Management System** - End-to-end quotation -> purchase -> delivery -> invoice -> dispatch workflow

#### Database Schema

- `accounts.User` - Custom user with roles and 2FA
- `companies.Company` - Organization management
- `companies.Division` - Department/division within company
- `companies.Location` - Physical locations with hierarchy
- `companies.CompanyUser` - User-Company associations
- `assets.AssetCategory` - Asset categorization
- `assets.AssetBrand` - Brand/manufacturer management
- `assets.AssetModel` - Product models within brands
- `assets.Asset` - Main asset model with full lifecycle
- `assets.AssetAssignment` - Assignment history tracking
- `assets.AssetMaintenance` - Maintenance scheduling and records
- `audit.*` - Audit logging models

---

## TODO

### High Priority

- [x] **2FA Implementation** - Complete TOTP setup and verification workflow
- [x] **Advanced Reporting** - Charts and analytics dashboard with filtering
- [x] **Enhanced Mobile Features** - Barcode scanning and offline capability
- [x] **REST API Development** - API endpoints for mobile integration
- [x] **Quotation & Invoice System** - Full workflow from quotation to invoice (see [Quotation & Invoice Management System](#quotation--invoice-management-system))

### Medium Priority

- [ ] **Performance Optimization** - Query optimization and caching
- [ ] **Maintenance Scheduling** - Automatic scheduling and notifications
- [ ] **Depreciation Enhancement** - Detailed depreciation reports
- [ ] **Workflow Automation** - Automated notifications for warranty expiry

### Future Features

- [ ] **WeChat Mini Program Integration**
  - Device audit/inspection for admins and field engineers
  - Quick item lookup (admins)
  - Quick item addition (admins)
  - Barcode scanning support

- [ ] **Write-off Processing** - Formal asset disposal workflow
- [ ] **Bulk Assignment/Return Reports** - Report generation for bulk operations
- [ ] **Photo-based Audit** - Audit with updated asset photos, SN, asset numbers
- [ ] **Grouped Auditing** - Audit by company and location

### Known Bugs

- [ ] Fix view pages: replace `assigned_at`, `returned_at`, `maintenance_date` with `assign_date`, `return_date`, `scheduled_at`

## Quotation & Invoice Management System

### Overview

A complete business workflow for managing quotations, purchase orders, deliveries, and invoices, integrated with the asset management system. Products are purchased after client confirms quotations, then added to inventory as assets upon receipt, and dispatched to stores/offices with delivery orders.

### Future Reference Summary

- Scope delivered in v0.1.0: end-to-end workflow from quotation creation to client dispatch and Esker forwarding.
- Core workflow stages: quotation (draft/sent/confirmed) -> purchase conversion and receipt -> delivery dispatch and signed completion -> invoice batch import/recalculation/document generation -> email dispatch tracking.
- Key data extensions: `products.ProductPrice`, `customers.CustomerProfile`, `quotations.Quotation*`, `purchases.PurchaseOrder*`, `deliveries.DeliveryOrder*`, `invoices.WeeklyOrderBatch`, `invoices.InvoiceInfo*`, `invoices.EmailDispatch`, `invoices.WorkflowStatusAudit`.
- Key automation paths: quotation PDF generation, delivery template document generation, invoice information template generation with PDF fallback, and bulk weekly Sharepoint import.
- Workflow governance: dashboard Kanban, cross-entity workflow search, status badge standardization, and status-change audit trail.
- Operational validation baseline: full smoke transition run verified quotation -> purchase -> delivery -> invoice -> dispatch transitions in Django test client flow.

### Integration with Asset Management

The system leverages existing HengJi AMS infrastructure:

| Existing Component | Used For |
|-------------------|----------|
| `assets.AssetBrand` | Product brands (repurposed for product catalog) |
| `assets.AssetModel` | Product models with pricing |
| `companies.Company` | Customer companies |
| `customers.CustomerProfile` | Customer contacts and delivery defaults (attn, tel, address) |
| `assets.Asset` | Purchased products added as assets |
| `assets.AssetAssignment` | Dispatch to stores/offices |

### Business Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUOTATION WORKFLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

  1. QUOTATION CREATION
     ├── Select customer (from Company)
     ├── Select products (from AssetBrand/AssetModel with pricing)
     ├── Set quotation date, validity period
     └── Generate PDF from "quotation template.xlsx"

  2. ATTACHMENTS (per quotation)
     ├── Invoice PDF
     ├── Invoice OFD
     ├── Invoice XML (zipped)
     └── Email confirmation screenshot

  3. CLIENT CONFIRMATION
     └── Status: Quotation Confirmed → Ready for Purchase

  4. PURCHASE & RECEIPT
     ├── Purchase confirmed products
     ├── Add products as Assets (AssetModel → Asset)
     └── Status: Stock Received

  5. DISPATCH & DELIVERY
     ├── Assign received assets to store/office location
     ├── Generate 签收单 PDF from "签收单 template.xlsx"
     └── Status: Dispatched → Awaiting Signed Copy

  6. DELIVERY CONFIRMATION
     └── Receive signed 签收单 → Status: Delivered

  7. WEEKLY INVOICE PROCESSING (Sharepoint)
     ├── Import completed orders from Sharepoint Excel
     ├── Sort orders per Excel sequence
     ├── Fill invoice numbers (yymmdd+##) and dates
     └── Status: Ready for Invoice

  8. INVOICE INFORMATION SHEET
     ├── Generate from "invoice information template.xlsx"
     ├── Fill: Bill To, PI Number, Amounts, PO/IO/SAP fields
     └── Status: Invoice Generated

  9. EMAIL DISPATCH
     ├── Send all documents to client
     ├── Client confirms integrity
     └── Forward to client's Esker system
```

### Data Models

#### Products (extends existing AssetBrand/AssetModel)

The product price list uses existing `AssetBrand` and `AssetModel` with extensions:

| Model | Fields |
|-------|--------|
| `ProductPrice` | `brand` (FK→AssetBrand), `model` (FK→AssetModel), `unit`, `price_without_tax`, `price_with_tax`, `tax_rate`, `is_current` |

#### Customers (extends existing Company)

| Model | Fields |
|-------|--------|
| `CustomerProfile` | `company` (OneToOne→Company), `contact_person`, `phone`, `email`, `delivery_address`, `delivery_city`, `delivery_contact`, `delivery_phone`, `delivery_method`, `tax_id` |

#### Quotations

| Model | Fields |
|-------|--------|
| `Quotation` | `quotation_number`, `customer`, `quotation_date`, `valid_until`, `attn`, `tel`, `status`, `total_without_tax`, `total_with_tax`, `notes` |
| `QuotationItem` | `quotation` (FK), `brand`, `product_description`, `user_brand`, `user_name`, `unit`, `quantity`, `price_without_tax`, `price_with_tax`, `tax_amount`, `line_total` |
| `QuotationAttachment` | `quotation` (FK), `attachment_type` (invoice_pdf/invoice_ofd/invoice_xml/email_confirm), `file`, `uploaded_at`, `notes` |

#### Deliveries

| Model | Fields |
|-------|--------|
| `DeliveryOrder` | `delivery_number`, `quotation`, `delivery_date`, `收货人`, `电话`, `交货地址`, `交货方式`, `status`, `signed_file`, `remarks` |
| `DeliveryItem` | `delivery_order` (FK), `asset` (FK→Asset), `serial_number`, `brand`, `product_description`, `user_brand`, `user_name`, `quantity` |

#### Invoices

| Model | Fields |
|-------|--------|
| `WeeklyOrderBatch` | `batch_id`, `sharepoint_file`, `uploaded_at`, `processed_at`, `status` |
| `InvoiceInfo` | `invoice_number` (yymmdd+##), `invoice_date`, `payment_due_date`, `bill_to`, `kering_group_po_number`, `internal_order`, `sap_cost_center`, `total_amount`, `net_amount`, `tax_amount`, `gross_amount`, `tax_rate`, `weekly_batch` (FK) |
| `InvoiceInfoItem` | `invoice_info` (FK), `description`, `unit_price`, `quantity`, `total_price`, `net_amount`, `tax_amount`, `gross_amount` |
| `EmailDispatch` | `quotation` (FK), `sent_to`, `cc`, `sent_at`, `esker_sent`, `esker_sent_at`, `attachments` (JSON), `status` |

### Template Files

| Template | Purpose | Key Fields |
|----------|---------|------------|
| `quotation template.xlsx` | Customer quote | date, quote date, validity, attn, tel, products, prices, totals |
| `签收单 template.xlsx` | Delivery receipt | 订货方, 收货人, 电话, serial numbers, brand, description, quantity, delivery address/method |
| `invoice information template.xlsx` | Invoice info sheet | Bill To, PI Number, Invoice Date, Due Date, amounts, PO Number, SAP Cost Center, line items |

### Implementation Tasks

#### Phase Q1: Database Extension - Products & Customers

- [x] **Q1.1** - Create `ProductPrice` model extending `AssetBrand`/`AssetModel`
  - Add `price_without_tax`, `price_with_tax`, `tax_rate`, `unit`, `is_current` fields
  - Create admin interface for price management

- [x] **Q1.2** - Create `CustomerProfile` model extending `Company`
  - Add delivery info fields: `delivery_address`, `delivery_city`, `delivery_contact`, `delivery_phone`, `delivery_method`
  - Add contact fields: `contact_person`, `phone`, `email`

- [x] **Q1.3** - Create product price list view with filtering by brand
- [x] **Q1.4** - Create customer profile view linked to Company
- [x] **Q1.5** - Add Excel import for bulk product pricing updates

#### Phase Q2: Quotation System

- [x] **Q2.1** - Create `Quotation` model
  - Auto-generate `quotation_number` (QT-YYYYMMDD-### format)
  - Fields: `customer`, `quotation_date`, `valid_until`, `attn`, `tel`, `status`, `total_without_tax`, `total_with_tax`, `notes`
  - Status: `draft`, `sent`, `confirmed`, `expired`, `cancelled`

- [x] **Q2.2** - Create `QuotationItem` model
  - Link to `ProductPrice` for product info
  - Calculate line totals with tax

- [x] **Q2.3** - Create quotation creation view
  - Select customer → Auto-fill attn/tel from CustomerProfile
  - Add line items with product selection
  - Auto-calculate totals

- [x] **Q2.4** - Generate quotation PDF from template
  - Map fields: date, quote date, validity, attn, tel
  - Map products: brand, description, user's brand, user, unit, prices, amounts
  - Calculate: total without tax, total with tax

- [x] **Q2.5** - Create quotation list view with status filtering and search
- [x] **Q2.6** - Add quotation actions: Edit, Duplicate, Cancel, Generate PDF

#### Phase Q3: Attachment Management

- [x] **Q3.1** - Create `QuotationAttachment` model
  - Attachment types: `invoice_pdf`, `invoice_ofd`, `invoice_xml`, `email_confirmation`
  - Store file path and upload timestamp

- [x] **Q3.2** - Add attachment upload interface on quotation detail
- [x] **Q3.3** - Add attachment preview and download
- [x] **Q3.4** - Validate file types (PDF, OFD, ZIP only)

#### Phase Q4: Purchase & Stock Management

- [x] **Q4.1** - Create "Convert to Purchase Order" action
  - Copy confirmed quotation items
  - Create Asset entries from products (using AssetModel)

- [x] **Q4.2** - Add purchase receipt view
  - Input serial numbers for each asset
  - Set initial location/status (received → ready for dispatch)

- [x] **Q4.3** - Link purchased assets back to source quotation
- [x] **Q4.4** - Add stock overview dashboard showing received products

#### Phase Q5: Delivery Order (签收单)

- [x] **Q5.1** - Create `DeliveryOrder` model
  - Auto-generate `delivery_number` (DO-YYYYMMDD-###)
  - Pull customer delivery info from `CustomerProfile`
  - Status: `pending`, `prepared`, `dispatched`, `completed`

- [x] **Q5.2** - Create `DeliveryItem` model
  - Link to `Asset` for serial number tracking

- [x] **Q5.3** - Generate 签收单 PDF from template
  - Map fields: 订货方, 收货人, 电话, 序列号, 品牌, 商品描述, 采购方品牌, 采购方用户, 数量, 交货地址, 交货方式

- [x] **Q5.4** - Add serial number input for each delivery item
- [x] **Q5.5** - Add signed 签收单 upload functionality
- [x] **Q5.6** - Create delivery order list with status tracking

#### Phase Q6: Weekly Sharepoint Processing

- [x] **Q6.1** - Create `WeeklyOrderBatch` model
  - Store Sharepoint Excel file reference
  - Track: `uploaded_at`, `processed_at`, `status`

- [x] **Q6.2** - Create Sharepoint Excel import view
  - Parse Excel for completed orders
  - Extract: Kering Group PO Number, Internal Order, SAP Cost Center

- [x] **Q6.3** - Implement invoice number auto-generation
  - Format: `yymmdd+##` (e.g., 26041501 for first invoice on Apr 15, 2026)
  - Track daily counter for `##` increment

- [x] **Q6.4** - Auto-fill invoice date from processing date
- [x] **Q6.5** - Create weekly batch list view showing processing status

#### Phase Q7: Invoice Information Sheet

- [x] **Q7.1** - Create `InvoiceInfo` model
  - Generate `invoice_number` (yymmdd+##)
  - Fields: `bill_to` (from brand), `kering_group_po_number`, `internal_order`, `sap_cost_center`
  - Amount fields: `total_amount`, `net_amount`, `tax_amount`, `gross_amount`, `tax_rate`

- [x] **Q7.2** - Create `InvoiceInfoItem` model
  - Line items: description, unit_price, quantity, totals

- [x] **Q7.3** - Generate invoice info PDF from template
  - All invoice fields with proper formatting
  - Line item table with tax breakdown

- [x] **Q7.4** - Auto-calculate totals from linked delivery items
- [x] **Q7.5** - Create invoice info list with export functionality

#### Phase Q8: Email Integration

- [x] **Q8.1** - Create email template for client dispatch
  - Include all attachments (quotation, delivery, invoice)
  - Support multiple recipients, CC, BCC

- [x] **Q8.2** - Create `EmailDispatch` model for tracking
  - Store: `sent_to`, `cc`, `sent_at`, `attachments`, `status`
  - Track Esker forwarding separately

- [x] **Q8.3** - Add email composition and sending interface
  - Preview email before sending
  - Attach all related documents automatically

- [x] **Q8.4** - Add "Client Confirmed" button to trigger Esker send
- [x] **Q8.5** - Create email history log per quotation

#### Phase Q9: Integration & Workflow Dashboard

- [x] **Q9.1** - Create workflow dashboard
  - Visual Kanban: Quotations → Confirmed → Purchased → Dispatched → Delivered → Invoiced
  - Show counts and values at each stage

- [x] **Q9.2** - Add "Next Action" suggestions on each entity
- [x] **Q9.3** - Add status badges with color coding throughout UI
- [x] **Q9.4** - Create audit trail for all status changes
- [x] **Q9.5** - Add search across quotations, deliveries, invoices

---

## Test Accounts

| Username | Password | Role |
|----------|----------|------|
| `testuser` | `testpass123` | Viewer |
| `admin` | `hjadmpass` | Superadmin |

### Database Credentials (PostgreSQL)

| Field | Value |
|-------|-------|
| Database | `hengjiams_db` |
| Username | `hengjiamsdjango` |
| Password | `hengjiams_djangopass` |
| Host | `127.0.0.1:5433` |

---

## Documentation

- [Changelog v0.0.1](docs/CHANGELOG_v0.0.1.md)
- [Changelog v0.0.2](docs/CHANGELOG_v0.0.2.md)
- [Changelog v0.0.3](docs/CHANGELOG_v0.0.3.md)
- [Changelog v0.0.4](docs/CHANGELOG_v0.0.4.md)
- [Development Notes](notes.md)

---

## Development Guidelines

1. **Coding Standards**
   - Django best practices
   - Extensive comments for maintainability
   - Bootstrap 5 responsive design

2. **Environment**
   - Use Conda environment `HengjiAMS1`
   - SQLite for development, PostgreSQL for production
   - Docker deployment planned

3. **Branching**
   - Work in feature branches
   - Commit message convention: clear, descriptive

---

*Last Updated: April 2026*
*HengJi Asset Management System v0.1.0*
