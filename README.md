# QR Code Asset Verification — Asset Verify

Asset Verify is a Flask web application for tracking equipment, generating QR labels, and recording physical asset-verification checks. The code is organized by feature so that contributors can find and maintain each part of the application.

## Features

- Password-hashed sign-in, optional authenticator MFA, and administrator-managed technician permissions.
- Add, view, search, and edit assets; technicians can submit new assets for administrator approval.
- Generate, download, print, and scan QR labels. QR image bytes are stored in MySQL.
- Require a condition photo when a verification marks an asset damaged or under repair.
- Preview bulk CSV files before upload; filter asset and verification lists.
- Filter verification history by preset or custom dates and download CSV reports.
- Send SMTP email alerts for technician asset requests and review requests in the administrator portal.
- View database-backed counts and dashboard charts. Asset deletion is not available in the portal.

## Technologies

Python 3, Flask, Flask-SQLAlchemy, Flask-Login, MySQL/PyMySQL (SQLite for local development and automated checks), Werkzeug, PyOTP, qrcode/Pillow, SMTP, Jinja templates, HTML, CSS, JavaScript, Chart.js, and html5-qrcode.

## Project structure

```text
QR-Asset-Verification/
├── app.py
├── back/                         # Backend features, models, database and config
├── front/                        # Jinja templates, CSS and JavaScript
├── docs/                         # Setup, architecture and user guide
├── CODE_LINKS/                   # Quick code map for a project walkthrough
├── tests/                        # Automated checks
├── qr_codes/                     # Legacy QR files used for migration
├── backups/                      # Local backups (not committed)
├── requirements.txt
├── .env.example                  # Safe configuration template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── START_ASSETVERIFY.bat         # Windows launcher for local setup
```

For a code tour, open [CODE_LINKS/README.md](CODE_LINKS/README.md). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the architecture diagram and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for application usage.

## Choose how to run the project

There are two supported setup approaches. **Choose one**: Docker (recommended for most downloaders) or manual Python + MySQL setup. You do not need to use both.

### Option A — Docker (recommended)

Docker runs the Flask application and MySQL database in containers, so you do not need to install Python or MySQL separately on your computer.

**Requirements:** Git and Docker Desktop. Start Docker Desktop before continuing.

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/nikhil-vaddeboina/QR-Code-Asset-Verification.git
   cd QR-Code-Asset-Verification
   ```

2. Create your own local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Open `.env` and replace the placeholder values. At minimum, set unique values for `SECRET_KEY`, `MFA_ENCRYPTION_KEY`, `ADMIN_PASSWORD`, `MYSQL_PASSWORD`, and `MYSQL_ROOT_PASSWORD`. Use a valid Fernet key for `MFA_ENCRYPTION_KEY`. Keep the MySQL passwords alphanumeric to avoid URL parsing issues. Do not commit or share `.env`.

4. Build and start the application:

   ```powershell
   docker compose up --build
   ```

5. When the containers finish starting, open <http://localhost:5013> in your browser. The container startup command initializes the database and creates the initial administrator account.

6. To stop the running containers, press `Ctrl+C`. You can also run `docker compose down` in another terminal. Database data is stored in the Docker volume named `mysql_data` and is retained when containers are stopped. **Only** run `docker compose down -v` if you intentionally want to delete that database volume and its data.

Optional: configure the `SMTP_*` and `ASSET_APPROVAL_EMAIL` values in `.env` if you want email notifications. For Gmail, use an App Password rather than your normal account password. Email notifications will not be sent if SMTP settings are blank or invalid; requests can still be reviewed in the administrator portal.

### Option B — Manual setup with Python + MySQL

Choose this option if you prefer to install and manage Python and MySQL directly on your computer.

**Requirements:** Python 3.10 or newer and MySQL 8. Install and start MySQL before continuing.

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/nikhil-vaddeboina/QR-Code-Asset-Verification.git
   cd QR-Code-Asset-Verification
   ```

2. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Open `.env` and configure your local MySQL connection in `DATABASE_URL`. The database and MySQL user specified in the URL must already exist and have the required permissions. Set your own `SECRET_KEY`, valid `MFA_ENCRYPTION_KEY`, and strong `ADMIN_PASSWORD`. Do not commit or share `.env`.

   Example format for the database URL (replace the example values with your own):

   ```text
   DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@127.0.0.1:3306/DATABASE_NAME?charset=utf8mb4
   ```

5. Initialize the database and initial administrator account:

   ```powershell
   flask --app app init-db
   ```

6. Start the application:

   ```powershell
   python app.py
   ```

   Alternatively, on Windows, double-click `START_ASSETVERIFY.bat` after configuring `.env`.

7. Open <http://127.0.0.1:5013> in Chrome or Edge.

Optional: configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `ASSET_APPROVAL_EMAIL` in `.env` to enable email notifications. For Gmail, use an App Password. If SMTP settings are blank or invalid, requests can still be reviewed in the administrator portal, but email cannot be sent.

## Database commands

Run these commands from the project folder with the virtual environment activated and the correct `.env` configuration loaded:

- `flask --app app init-db` creates the tables and initial administrator account.
- `flask --app app seed-demo` adds demo assets, checks, and QR images.
- `flask --app app setup-demo` initializes the database and adds demo records.
- `flask --app app migrate-qrs-to-db` imports legacy QR PNGs and generates missing labels.
- `flask --app app generate-qrs` creates QR images for assets that do not yet have one in MySQL.

The QR images are stored in the `asset_qr_codes.qr_image` database column. The `qr_codes/` folder is retained for importing older local QR images.

## Tests

The pytest checks use a temporary SQLite database. Run:

```powershell
pytest
```

The tests are designed not to modify the configured MySQL database.

## Security and data notes

- Never commit `.env`, database passwords, secret keys, local database files, personal data, or database backups.
- `.env.example` is a template only. Each person should create their own `.env` and use their own credentials.
- Demo data is separate from your private/local database records. Do not use real asset or employee information in a public repository.
- Docker's `mysql_data` volume stores data on the computer running Docker; it is not uploaded to GitHub.
