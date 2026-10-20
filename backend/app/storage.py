"""Initialize local scan storage, preserving databases from the account edition."""
from sqlalchemy import inspect, text

from app import db
from app.models.scan import Scan


def initialize_storage():
    engine = db.engine
    with engine.connect() as connection:
        # SQLite DDL needs an explicit transaction for atomic rename/create/copy.
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            schema = inspect(connection)
            tables = schema.get_table_names()
            source_columns = {column["name"] for column in schema.get_columns("scan")} if "scan" in tables else set()
            if "user_id" in source_columns:
                if engine.dialect.name != "sqlite":
                    raise RuntimeError("Legacy migration supports SQLite only. Back up and migrate this database manually.")
                if "scan_legacy_auth" in tables:
                    raise RuntimeError("Migration stopped: scan_legacy_auth already exists. Back up and inspect the database.")
                missing = {column.name for column in Scan.__table__.columns} - source_columns
                if missing:
                    raise RuntimeError("Migration stopped: legacy scan columns missing: " + ", ".join(sorted(missing)))
                connection.exec_driver_sql("ALTER TABLE scan RENAME TO scan_legacy_auth")
                Scan.__table__.create(connection)
                columns = ", ".join(f'"{column.name}"' for column in Scan.__table__.columns)
                connection.exec_driver_sql(
                    f"INSERT INTO scan ({columns}) SELECT {columns} FROM scan_legacy_auth"
                )
                old_count = connection.scalar(text("SELECT count(*) FROM scan_legacy_auth"))
                new_count = connection.scalar(text("SELECT count(*) FROM scan"))
                if old_count != new_count:
                    raise RuntimeError("Migration row-count mismatch; all changes rolled back.")
            else:
                db.metadata.create_all(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
