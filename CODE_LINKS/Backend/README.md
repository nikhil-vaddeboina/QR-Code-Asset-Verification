# Backend files

The backend handles requests, business rules, QR creation, sign-in, and communication with MySQL.

## Main application and database models

- [Flask app, setup, and database commands](../../app.py)
- [Asset and QR image database models](../../back/models/asset.py)
- [User model](../../back/models/user.py)
- [Verification model](../../back/models/verification.py)

## Request handling

- [Asset creation, bulk upload, QR display and download](../../back/routes/assets.py)
- [Sign-in routes](../../back/routes/auth.py)
- [Dashboard routes](../../back/routes/dashboard.py)
- [QR lookup and verification routes](../../back/routes/verification.py)
- [History routes](../../back/routes/history.py)

## Backend services

- [QR image generation and MySQL storage](../../back/services/qr_service.py)
- [Asset validation and ID allocation](../../back/services/asset_service.py)
- [Verification recording](../../back/services/verification_service.py)
- [Demo data creation](../../back/services/seed_service.py)

The QR PNG is stored in MySQL in `asset_qr_codes.qr_image`. The frontend asks the backend for that image when it displays or downloads a QR label.
