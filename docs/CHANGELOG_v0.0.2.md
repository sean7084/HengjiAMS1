# Release Notes and Progress Report for Version 0.0.2

---

## Release Notes for Version 0.0.2

### Key Enhancements and New Features

#### 1. Asset Models

- Re-enabled and fixed the models in the assets application.

#### 2. Audit System

- Re-enabled and fixed the models in the audit application.

#### 3. Dashboard

- Created the main dashboard for users after login.
- Updated the dashboard to display sample assets and provide real-time data.

#### 4. Additional Templates

- Added templates for:
  - Two-Factor Authentication (2FA) setup.
  - Profile and settings pages.
  - Company and user management pages.
  - Admin pages for companies, divisions, locations, and audit logs.

#### 5. Asset Import/Export

- Introduced CSV and Excel import/export functionality for assets.

#### 6. Reporting System

- Implemented charts and analytics for enhanced reporting capabilities.

#### 7. Mobile Optimization

- Added barcode scanning support for mobile devices.

#### 8. Role-Based Access Control

- Defined and implemented four administrator roles:
  - **Superadmin**: Access to all data.
  - **Manager**: Access to all assets in their company.
  - **IT Specialist**: Access to assets in one or multiple divisions within their company.
  - **Viewer**: Read-only access to specific locations within their company.

#### 9. Language Support

- Completed English and Chinese language support for all HTML templates.

---

### Fixes and Adjustments

#### 1. QR Code for 2FA

- Resolved an issue where the QR code was not displayed on the 2FA setup page (`/accounts/2fa/setup-simple/`).

#### 2. Navigation and URLs

- Updated the dashboard URL to `/dashboard` (previously `/`).
- Ensured all key components (e.g., dashboard, asset management, audit, location management, reports, user management) are accessible via the navigation pane.

#### 3. User Roles Display

- Fixed an issue where user roles were displayed as "Staff" instead of their actual roles.

#### 4. Default Templates for Admin Pages

- Updated default Django admin templates to align with the base template's style.
- Introduced new pages for:
  - `/companies/`
  - `/companies/division/`
  - `/companies/location/`
  - `/audit/auditlog/`
  - `/audit/assetaudit/`
  - `/audit/systemevent/`

#### 5. Asset Visibility

- Ensured asset visibility on the dashboard matches user permissions on the assets page.

#### 6. Legacy Role Removal

- Removed legacy role support and references from all relevant pages.

---

### Merges and Consolidations

- Merged `assets/urls_old.py` with `assets/urls.py` for extended support.
- Merged `audit/urls_old.py` with `audit/urls_new.py` to finalize URL development for the audit app.
- Consolidated `PROGRESS_REPORT_v0.0.1.md` with `docs/PROGRESS_REPORT_v0.0.1.md` and `docs/v0.0.1.md`.

---

### Known Issues

1. **Method Not Allowed (GET): `/zh-hans/accounts/logout/`**
   - Logout functionality for Chinese language support needs further investigation.

2. **Default Passwords for New Users**
   - On `/zh-hans/accounts/users/create/`, newly created users should have:
     - A default random password.
     - An option to require password change on the next login (enabled by default).

3. **Python Version Compatibility**
   - Compatibility with Python 3.13 is under review. Updating without confirmation may cause issues.

---

### Testing Notes

- Use the admin account for testing:
  - **Username**: `admin`
  - **Password**: `hjadmpass`
- Sample assets have been generated for testing purposes.

---

### Rollbacks

- Reverted changes to admin pages (`/admin/companies/...`, `/admin/audit/...`) that aligned them with the base template's style. Instead, focused on creating new user-facing pages aligned with the base template.

---

## HengJi AMS Development Progress Report v0.0.2

**Date:** July 8, 2025  
**Focus:** Complete Implementation of Core Asset & Company Management Systems

---

### 🎯 Overview

Building on the foundation of v0.0.1, this development cycle focused on implementing the primary business logic of the HengJi AMS. Version 0.0.2 delivers a fully functional, end-to-end asset management system and the complete company/location organizational structure.

---

### ✅ Completed Components in This Iteration

#### 1. Asset Management System - Full Implementation

- **Core Models**: Implemented the full suite of asset-related models: `AssetCategory`, `AssetBrand`, `Asset`, `AssetAssignment`, and `AssetMaintenance`.

- **CRUD Functionality**: Delivered a complete user-facing interface for creating, reading, updating, and retiring assets.

- **Advanced Features**:
  - **Search & Filter**: Implemented an advanced search form for filtering assets.
  - **Assignment Tracking**: Developed views for assigning assets to users and processing returns.
  - **Data Export**: Added functionality to export asset lists to CSV.

- **UI/UX**: Created modern, responsive, and user-friendly templates for asset lists, details, and forms using Bootstrap 5.

#### 2. Company & Location Structure - Full Implementation

- **Core Models**: Implemented the `Company`, `Division`, and hierarchical `Location` models to structure the organization.

- **Admin Interface**: Configured the Django admin for easy management of companies, divisions, and locations.

- **Data Integrity**: Ensured all relationships between assets, users, and locations are correctly established.

#### 3. Audit System Integration

- **Enabled Audit App**: With all core models in place, the `audit` app was successfully integrated.

- **Automated Logging**: The system now automatically logs all creation, update, and deletion events for assets, providing a complete audit trail for compliance.

#### 4. UI & Navigation Enhancements

- **Updated Main Navigation**: The base template now includes navigation links to the new asset management sections.

- **Status Indicators**: Implemented color-coded badges for asset statuses (e.g., Available, Assigned) for improved clarity.

- **Data Synchronization**: Ensured all field names across models, forms, and templates are consistent.

---

### 🚀 System Status: Core Functionality Complete

The system is now operational with the following end-to-end features:

1. User Authentication & Management (from v0.0.1)
2. Company, Division & Location Management
3. Complete Asset Lifecycle Management (CRUD)
4. Asset Assignment & Return Tracking
5. Data Export to CSV
6. Comprehensive Audit Trail

---

### 📈 Next Steps (v0.0.3 Roadmap)

#### High Priority

1. **2FA Implementation**: Complete the user setup and verification workflow.
2. **Reporting & Dashboard**: Build out the main dashboard with asset analytics and charts.
3. **Company Management Views**: Create a user-facing UI for managing locations.

#### Medium Priority

1. **Asset Data Import**: Implement CSV/Excel import functionality.
2. **Mobile Optimization**: Enhance mobile views and prepare for barcode scanning integration.

---

### 🏁 Conclusion

Version 0.0.2 marks a major milestone, transforming the project from a foundational shell into a fully functional asset management system. The core business requirements are now met, providing a stable platform for building advanced features.
