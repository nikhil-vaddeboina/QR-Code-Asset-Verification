# Asset Verify — QR Asset Verification & Management

Asset Verify is a Flask web app for tracking equipment, generating QR labels, and recording physical verification checks. Its code is arranged by feature so the team can find each part without searching through one large folder.

## Features

- Password-hashed sign-in, optional authenticator MFA, and administrator-managed technician permissions.
- Add, view, search, and edit assets; technicians can submit new assets for administrator approval.
- Generate, download, print, and scan QR labels. QR image bytes are stored in MySQL.
- Require a condition photo when a verification marks an asset damaged or under repair.
- Preview bulk CSV files before upload; filter asset and verification lists as selections change.
- Filter history by preset or custom dates, choose rows per page, and download CSV reports.
- Send SMTP email alerts for technician asset requests and review them in the administrator portal.
- View database-backed counts and dashboard charts. Asset deletion is not available in the portal.

## Technologies

Python 3, Flask, Flask-SQLAlchemy, Flask-Login, MySQL/PyMySQL (SQLite for local development and automated checks), Werkzeug, PyOTP, qrcode/Pillow, SMTP, Jinja templates, HTML, CSS, JavaScript, Chart.js, and html5-qrcode.

## Project structure

```text
QR-Asset-Verification/
├── app.py                         # App setup, shared extensions and CLI commands
├── back/
│   ├── features/                  # One folder per app feature
│   │   ├── assets/                # Asset routes, validation/service, QR generation
│   │   ├── authentication/        # Login, password and MFA routes
│   │   ├── access/                # Role and permission checks
│   │   ├── dashboard/             # Dashboard route and statistics
│   │   ├── history/               # Verification history route
│   │   ├── team/                  # Technician creation, access, deletion
│   │   ├── verification/          # Scanner pages and verification logic
│   │   └── demo/                  # Demo-data creation
│   ├── models/                    # Database tables/entities
│   ├── database/                  # Reference schema and SQL seed data
│   └── config/                    # Configuration reference
├── front/
│   ├── templates/                 # Jinja pages grouped by feature
│   └── static/                    # Shared styles and feature-specific scripts
├── docs/                          # Setup, architecture, and user guide
├── CODE_LINKS/                    # Quick code map for presenting the project
├── tests/                         # Automated checks
├── qr_codes/                      # Legacy QR files kept for database migration
├── requirements.txt
├── .env                           # Local secrets; do not share or commit
└── START_ASSETVERIFY.bat          # Windows launcher
```

For an easy code tour, open [CODE_LINKS/README.md](CODE_LINKS/README.md). The architecture diagram is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run on Windows

1. Install Python 3.10+ and MySQL 8 if you plan to use MySQL.
2. Open this folder in VS Code. In its terminal, create and activate a virtual environment, then install packages:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Set your local `.env` values. Do not share `.env` or put its passwords in the launcher file. The app can also start with SQLite for local practice.
   To email administrators about technician asset requests, fill in `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `ASSET_APPROVAL_EMAIL`. For Gmail, use an App Password. If the values are blank or invalid, the request is still saved for review in the admin portal, but the email cannot be sent.
4. Initialize the database and administrator account:

   ```powershell
   flask --app app init-db
   ```

5. Start the app with `python app.py`, or double-click `START_ASSETVERIFY.bat`.
6. Open <http://127.0.0.1:5013> in Chrome or Edge.

See [docs/SETUP.md](docs/SETUP.md) for database setup and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for app usage. Change the local secret and administrator password before using real data.

## Database commands

- `flask --app app init-db` creates the tables and initial administrator account.
- `flask --app app seed-demo` adds demo assets, checks, and QR images.
- `flask --app app migrate-qrs-to-db` imports legacy QR PNGs and generates missing labels.
- `flask --app app generate-qrs` creates QR images for assets that do not yet have one in MySQL.
- `flask --app app setup-demo` initializes the database and adds demo records.

The QR images are saved in the `asset_qr_codes.qr_image` database column. The `qr_codes/` folder remains so old local images can be imported during migration.

## Tests

The project has pytest checks that use a temporary SQLite database. Run `pytest` when you want to check the app; the checks do not modify the configured MySQL database.

## Run with Docker (for teammates)

1. Install Docker Desktop and start it.
2. Copy `.env.example` to `.env`. Set unique values for `SECRET_KEY`, `ADMIN_PASSWORD`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD`. Keep the two MySQL passwords alphanumeric so the database URL parses correctly. Never commit or send `.env`.
3. From this project folder, run:

   ```powershell
   docker compose up --build
   ```

4. Open <http://localhost:5013>. The first startup creates the MySQL schema and administrator account. Docker Compose keeps database data in its `mysql_data` volume.
5. Stop the app with `Ctrl+C`. Use `docker compose down` to stop and `docker compose down -v` only if you intentionally want to erase the Docker database.

The app image is built from `Dockerfile`; `docker-compose.yml` runs it with MySQL. The local `.env`, virtual environment, backup archive, and exported QR PNGs are excluded from the image and Git. Database QR images remain in MySQL.

## GitHub / teammate download

After this project is pushed to a GitHub repository, a teammate can download it on another laptop with:

```powershell
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY
Copy-Item .env.example .env
```

They should fill in their own `.env`, install/start Docker Desktop, then run `docker compose up --build`. Replace `OWNER/REPOSITORY` with the actual GitHub account and repository name.
