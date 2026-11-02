# Setup guide (Windows, VS Code and MySQL)

## 1. Install Python and MySQL

Install Python 3.10 or newer and MySQL 8. During Python installation, enable the option to add Python to PATH. MySQL Workbench is optional but useful for viewing the database.

## 2. Open the project in VS Code

Open the `QR-Asset-Verification` folder. In the integrated terminal, confirm `python --version` works.

## 3. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

If PowerShell prevents activation for this terminal, use `Set-ExecutionPolicy -Scope Process Bypass` and activate again.

## 4. Install dependencies

```powershell
pip install -r requirements.txt
```

## 5. Create the MySQL database

In MySQL Workbench or the MySQL client, run:

```sql
CREATE DATABASE asset_verification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

The Flask setup command creates the tables. `back/database/schema.sql` is also supplied as a reference schema.

## 6. Configure environment variables

Copy `.env.example` to `.env` in the project root. Set `DATABASE_URL` with your MySQL password, for example:

```text
DATABASE_URL=mysql+pymysql://root:your_password@localhost/asset_verification?charset=utf8mb4
```

Set a long random `SECRET_KEY`. Set `ADMIN_PASSWORD` to the password you want for the initial `admin` account. A local SQLite option is `DATABASE_URL=sqlite:///asset_verification.db`.

## 7. Create tables and demo records

```powershell
flask --app app setup-demo
```

This creates the tables, the hashed administrator account, 100 assets, 180 verification records and matching QR images. The command can safely be repeated; it will not add a second demo set when the data is present. To run the schema and seeder separately, use `flask --app app init-db` and `flask --app app seed-demo`.

## 8. Start the application

```powershell
python app.py
```

Open <http://127.0.0.1:5000>. Sign in with `admin` and the configured `ADMIN_PASSWORD` (default: `admin123`).

## 9. Run automated tests

```powershell
pytest
```

Tests use a temporary SQLite database. They do not change the MySQL database in `.env`.
