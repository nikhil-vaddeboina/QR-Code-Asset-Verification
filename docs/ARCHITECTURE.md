# Asset Verify architecture

The app is a single Flask application organized into feature folders. The browser sends a request to the relevant Flask route. The route checks permissions and input, calls the feature service, and SQLAlchemy reads or writes the database.

```text
Browser pages and scripts (front/)
              ↓
Flask app setup and shared database session (app.py)
              ↓
Feature routes (back/features/<feature>/routes.py)
              ↓
Feature services (validation, QR generation, verification)
              ↓
Database models (back/models/)
              ↓
MySQL, or SQLite for local practice and automated checks
```

## Where each feature lives

| Feature | Browser pages | Flask/backend code |
|---|---|---|
| Assets and bulk upload | `front/templates/assets/` | `back/features/assets/` |
| Login, passwords, MFA | `front/templates/authentication/` | `back/features/authentication/` |
| Technician accounts and roles | `front/templates/team/` | `back/features/team/` and `back/features/access/` |
| Dashboard | `front/templates/dashboard/` | `back/features/dashboard/` |
| QR scanning and verification | `front/templates/verification/` | `back/features/verification/` |
| Verification history | `front/templates/history/` | `back/features/history/` |
| Shared layout and styles | `front/templates/shared/`, `front/static/css/shared/` | Shared app setup in `app.py` |

## Main data flow

1. A user opens a page or submits a form in the browser.
2. Flask routes the request to a feature folder and checks whether the signed-in user has permission.
3. The route validates submitted values and calls the feature's service code when needed.
4. SQLAlchemy models represent the `user`, `asset`, `verification`, and `asset_qr_codes` database tables.
5. The route returns a page or a QR image to the browser.

## Security notes

Passwords are stored as one-way Werkzeug password hashes and checked during sign-in. Technician permissions are enforced on the server, not just hidden in the page. MFA secrets are encrypted when configured. `.env` contains local secrets and must not be shared or committed.

## QR storage

The QR service creates a PNG image for an asset. New images are stored in MySQL as binary image data in `asset_qr_codes.qr_image`. The `qr_codes/` folder holds legacy PNG files for migration; it is not the primary storage for newly generated images.