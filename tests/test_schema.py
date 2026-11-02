from sqlalchemy import inspect, text

from app import db, ensure_user_permissions_column


def test_existing_user_table_is_upgraded_with_permissions_column(app):
    with app.app_context():
        db.drop_all()
        db.session.execute(text('CREATE TABLE "user" (id INTEGER PRIMARY KEY, username VARCHAR(80))'))
        db.session.commit()

        ensure_user_permissions_column()

        columns = {column["name"] for column in inspect(db.engine).get_columns("user")}
        assert "permissions" in columns


def test_init_db_command_upgrades_legacy_schema_before_querying_users(app):
    with app.app_context():
        db.drop_all()
        db.session.execute(text(
            'CREATE TABLE "user" ('
            'id INTEGER PRIMARY KEY, '
            'username VARCHAR(80) UNIQUE NOT NULL, '
            'password_hash VARCHAR(255) NOT NULL, '
            'role VARCHAR(40) NOT NULL, '
            'mfa_enabled BOOLEAN NOT NULL DEFAULT 0, '
            'mfa_secret_encrypted VARCHAR(255), '
            'created_at DATETIME NOT NULL'
            ')'
        ))
        db.session.commit()

    result = app.test_cli_runner().invoke(args=["init-db"])

    assert result.exit_code == 0, result.output
    with app.app_context():
        columns = {column["name"] for column in inspect(db.engine).get_columns("user")}
        assert "permissions" in columns
        from back.models import User
        assert User.query.filter_by(username="admin").one()
