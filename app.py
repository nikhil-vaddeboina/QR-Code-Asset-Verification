"""QR Asset Verification — Flask application factory and command-line setup."""
import os
from datetime import date, datetime, timedelta

import click
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, inspect, or_, text
from werkzeug.security import generate_password_hash

load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

STATUSES = ["Active", "Verified", "Damaged", "Missing", "Under Repair", "Transferred", "Retired"]
RESULTS = ["Verified", "Damaged", "Missing", "Under Repair", "Transferred"]
CATEGORIES = ["Computers", "Furniture", "Laboratory", "Networking", "Audio Visual", "Vehicles", "Office Equipment"]
DEPARTMENTS = ["Computer Science", "Administration", "Library", "Physics", "Electrical Engineering", "Student Services"]
LOCATIONS = ["Block A · 101", "Block A · 204", "Block B · Lab 1", "Block B · Lab 2", "Library · Ground Floor", "Admin · Room 12", "Workshop · 03"]


def ensure_user_permissions_column():
    """Add newer user and verification columns to an existing local database."""
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    dialect = db.engine.dialect.name
    if dialect not in {"mysql", "sqlite"}:
        raise RuntimeError(f"Automatic database upgrades are not supported for {dialect}.")

    additions = {
        "user": {
            "permissions": ("JSON NULL" if dialect == "mysql" else "JSON"),
            "email": ("VARCHAR(254) NULL" if dialect == "mysql" else "VARCHAR(254)"),
        },
        "verification": {
            "evidence_image": ("LONGBLOB NULL" if dialect == "mysql" else "BLOB"),
            "evidence_mime_type": ("VARCHAR(40) NULL" if dialect == "mysql" else "VARCHAR(40)"),
        },
    }
    with db.engine.begin() as connection:
        for table, columns in additions.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    if dialect == "mysql":
                        statement = text(f"ALTER TABLE `{table}` ADD COLUMN `{name}` {sql_type}")
                    else:
                        statement = text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}')
                    connection.execute(statement)

        if "asset" in tables:
            connection.execute(text(
                "UPDATE asset SET assigned_to = 'Unassigned' "
                "WHERE LOWER(TRIM(status)) = 'retired' "
                "AND LOWER(TRIM(assigned_to)) <> 'unassigned'"
            ))

        if "user" in tables:
            index_names = {index["name"] for index in inspector.get_indexes("user")}
            unique_email = any(set(item.get("column_names") or []) == {"email"} for item in inspector.get_unique_constraints("user"))
            if "uq_user_email" not in index_names and not unique_email:
                if dialect == "mysql":
                    connection.execute(text("CREATE UNIQUE INDEX `uq_user_email` ON `user` (`email`)"))
                else:
                    connection.execute(text('CREATE UNIQUE INDEX "uq_user_email" ON "user" ("email")'))


def is_werkzeug_password_hash(value):
    """Recognize password hashes produced by the Werkzeug algorithms used here."""
    return isinstance(value, str) and value.startswith(("scrypt:", "pbkdf2:")) and value.count("$") >= 2

from back.models import User, Asset, AssetQRCode, Verification, AssetRequest
from back.features.authentication.routes import auth_bp
from back.features.dashboard.routes import dashboard_bp
from back.features.assets.routes import assets_bp
from back.features.verification.routes import verification_bp
from back.features.history.routes import history_bp
from back.features.team.routes import team_bp
from back.features.assets.qr import create_qr, render_qr_png
from back.features.access.permissions import has_permission, is_administrator


def create_app(test_config=None):
    app = Flask(__name__, template_folder="front/templates", static_folder="front/static")
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "local-development-key-change-me"),
        MFA_ENCRYPTION_KEY=os.getenv("MFA_ENCRYPTION_KEY", ""),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///asset_verification.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        QR_FOLDER=os.path.join(app.root_path, "qr_codes"),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        SMTP_HOST=os.getenv("SMTP_HOST", ""),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"},
        SMTP_FROM=os.getenv("SMTP_FROM", ""),
        ASSET_APPROVAL_EMAIL=os.getenv("ASSET_APPROVAL_EMAIL", ""),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    for blueprint in (auth_bp, dashboard_bp, assets_bp, verification_bp, history_bp, team_bp):
        app.register_blueprint(blueprint)

    @app.get("/health/version")
    def app_version():
        return jsonify(version="retired-guard-20261102")

    @app.context_processor
    def inject_globals():
        return {"STATUSES": STATUSES, "CATEGORIES": CATEGORIES, "DEPARTMENTS": DEPARTMENTS, "LOCATIONS": LOCATIONS, "today": date.today().isoformat(), "is_admin": is_administrator(current_user), "can_access": lambda permission: has_permission(current_user, permission)}

    @app.errorhandler(404)
    def not_found(_):
        return render_template("shared/error.html", code=404, title="Page not found", message="The page you requested could not be found."), 404

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        return render_template("shared/error.html", code=500, title="Something went wrong", message="Please try again. If the problem continues, check your database connection."), 500

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("shared/error.html", code=403, title="Access restricted", message="Your account does not have permission to open this page."), 403

    @app.cli.command("init-db")
    def init_db():
        """Create tables, upgrade the user schema, and prepare the administrator account."""
        db.create_all()
        ensure_user_permissions_column()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123")), role="administrator"))
            db.session.commit()
        click.echo("Database tables are ready. Sign in as admin using the ADMIN_PASSWORD configured in .env.")

    @app.cli.command("hash-legacy-passwords")
    def hash_legacy_passwords():
        """Hash any legacy plain-text values in user.password_hash without displaying them."""
        ensure_user_permissions_column()
        hashed_count = 0
        skipped_empty = 0
        already_hashed = 0
        with db.engine.begin() as connection:
            rows = connection.execute(text("SELECT id, password_hash FROM `user`")).mappings().all()
            for row in rows:
                stored_value = row["password_hash"]
                if is_werkzeug_password_hash(stored_value):
                    already_hashed += 1
                elif not stored_value:
                    skipped_empty += 1
                else:
                    connection.execute(
                        text("UPDATE `user` SET password_hash = :password_hash WHERE id = :user_id"),
                        {"password_hash": generate_password_hash(stored_value), "user_id": row["id"]},
                    )
                    hashed_count += 1
        click.echo(
            f"Hashed {hashed_count} legacy password(s); "
            f"{already_hashed} were already hashed; {skipped_empty} empty value(s) were left unchanged."
        )

    @app.cli.command("seed-demo")
    def seed_demo():
        """Create 100 demo assets, QR images and 180 realistic verifications."""
        from back.features.demo.seed_service import seed_demo_data
        seed_demo_data(app)
        click.echo("Demo data ready: 100 assets, 180 verification records, and QR images.")

    @app.cli.command("generate-qrs")
    def generate_qrs():
        """Ensure every database asset has a QR PNG stored in MySQL."""
        assets = Asset.query.order_by(Asset.id).all()
        if not assets:
            click.echo("No assets found in the configured database.")
            return

        port = os.getenv("PORT", "5013")
        base_url = os.getenv("QR_BASE_URL", f"http://127.0.0.1:{port}")
        with app.test_request_context("/", base_url=base_url):
            for asset in assets:
                if AssetQRCode.query.filter_by(asset_pk=asset.id).first() is None:
                    create_qr(asset)

        stored = AssetQRCode.query.count()
        click.echo(f"MySQL contains QR images for {stored} assets ({len(assets)} assets total).")

    @app.cli.command("migrate-qrs-to-db")
    def migrate_qrs_to_db():
        """Copy existing QR PNG files into MySQL and generate any missing labels."""
        db.create_all()
        ensure_user_permissions_column()
        assets = Asset.query.order_by(Asset.id).all()
        if not assets:
            click.echo("No assets found in the configured database.")
            return

        port = os.getenv("PORT", "5013")
        base_url = os.getenv("QR_BASE_URL", f"http://127.0.0.1:{port}")
        imported = generated = skipped = 0
        try:
            with app.test_request_context("/", base_url=base_url):
                for asset in assets:
                    if AssetQRCode.query.filter_by(asset_pk=asset.id).first() is not None:
                        skipped += 1
                        continue
                    path = os.path.join(app.config["QR_FOLDER"], asset.qr_filename)
                    if os.path.isfile(path):
                        with open(path, "rb") as image_file:
                            image_bytes = image_file.read()
                        imported += 1
                    else:
                        image_bytes = render_qr_png(asset)
                        generated += 1
                    db.session.add(AssetQRCode(asset_pk=asset.id, qr_image=image_bytes, mime_type="image/png"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        stored = AssetQRCode.query.count()
        click.echo(f"Imported {imported} existing PNGs and generated {generated} missing QR images.")
        click.echo(f"MySQL now contains QR images for {stored} of {len(assets)} assets.")

    @app.cli.command("setup-demo")
    def setup_demo():
        """Convenience command: initialize tables then seed demo data."""
        db.create_all()
        ensure_user_permissions_column()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123")), role="administrator"))
            db.session.commit()
        from back.features.demo.seed_service import seed_demo_data
        seed_demo_data(app)
        click.echo("Setup complete. Sign in at /login using admin and the ADMIN_PASSWORD configured in .env.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5013")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
