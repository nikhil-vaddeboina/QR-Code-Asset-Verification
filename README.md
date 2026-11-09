# QR Code Asset Verification System — Asset Verify

## 1. Project Overview

Asset Verify is a web-based Asset Management and QR Code Verification System developed using Python Flask and MySQL.

The application helps organizations maintain their physical asset records, generate unique QR codes for assets, and perform asset verification through QR code scanning.

It provides a centralized platform for managing assets, monitoring their condition, recording verification activities, and managing technician requests.

## 2. Problem Statement

Traditional asset management processes often depend on spreadsheets and manual verification. These methods can lead to:
- Difficulty tracking large numbers of assets.
- Time-consuming physical verification.
- Inaccurate or outdated asset records.
- Difficulty identifying damaged or under-repair assets.
- Limited visibility into verification history.

The Asset Verify system aims to address these challenges through a centralized digital platform.

## 3. Project Objectives

- Maintain centralized asset information.
- Generate unique QR codes for registered assets.
- Simplify physical asset verification.
- Track asset conditions and verification history.
- Provide role-based access to application features.
- Support bulk asset registration.
- Improve asset tracking and reporting.

## 4. Key Features

### Dashboard
Provides an overview of asset inventory, asset status, verification activity, and important statistics.

### Asset Management
Allows authorized users to add, view, search, and update asset information.

### QR Code Generation
Generates QR labels for registered assets. QR codes can be downloaded, printed, and scanned during physical verification.

### Bulk Asset Upload
Supports CSV-based bulk asset registration with a preview before uploading records.

### Scan and Verify
Allows users to scan asset QR codes and record physical verification results.

### Verification History
Maintains verification records and provides date-based filtering and CSV report downloads.

### Technician Management
Allows administrators to manage technician accounts and their permissions.

### Asset Requests
Allows technicians to submit asset requests for administrator review and approval.

### Multi-Factor Authentication
Supports optional authenticator-based MFA for an additional layer of account security.

## 5. User Roles

### Administrator
- Manage asset records.
- Manage technician accounts and permissions.
- Review and approve technician asset requests.
- Access dashboard statistics and reports.
- Manage application-level security settings.

### Technician
- Access permitted asset management features.
- Submit asset requests for approval.
- Scan QR codes and perform asset verification.
- Record asset condition and verification information.

## 6. Application Workflow

1. An authorized user registers an asset in the application.
2. The system generates a unique QR code for the asset.
3. The QR code is downloaded or printed and attached to the physical asset.
4. A technician scans the QR code during physical verification.
5. The technician records the asset's verification status and condition.
6. Verification information is saved in the database.
7. Administrators can review asset information, verification history, and reports.

## 7. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3 |
| Backend Framework | Flask |
| Database | MySQL |
| Database Integration | Flask-SQLAlchemy, PyMySQL |
| Authentication | Flask-Login, Werkzeug |
| MFA | PyOTP, Cryptography |
| QR Code | qrcode, Pillow |
| Frontend | HTML, CSS, JavaScript |
| Templates | Jinja |
| Charts | Chart.js |
| QR Scanning | html5-qrcode |
| Testing | Pytest |
| Containerization | Docker, Docker Compose |

## 8. Database Overview

The application uses a relational database to maintain asset information, QR code data, user information, and verification records.

QR code image data is stored in the database, while the project also retains a folder for legacy QR image migration.

## 9. Security Features

- Password hashing for user authentication.
- Optional authenticator-based multi-factor authentication.
- Role-based access and permissions.
- Administrator approval workflow for technician asset requests.
- Environment-based application configuration.
- Sensitive configuration and credentials are excluded from the public repository.

## 10. Project Folder Structure

```text
QR-Asset-Verification/
│
├── app.py
├── back/
│   └── Backend features, models, database and configuration
│
├── front/
│   └── Frontend templates, CSS and JavaScript
│
├── docs/
│   └── Project documentation and user guide
│
├── CODE_LINKS/
│   └── Quick code reference
│
├── tests/
│   └── Automated tests
│
├── qr_codes/
│   └── Legacy QR images
│
├── backups/
│   └── Local backups (not committed)
│
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

## 11. Project Documentation

For additional technical information, refer to:

- `docs/ARCHITECTURE.md` — Application architecture.
- `docs/USER_GUIDE.md` — Application usage guide.
- `CODE_LINKS/README.md` — Quick code reference.

---

**Project:** QR Code Asset Verification System

**Application Name:** Asset Verify

**Backend:** Python Flask

**Database:** MySQL