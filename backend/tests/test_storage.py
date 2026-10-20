import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from sqlalchemy import inspect
from app import create_app, db
from app.models.scan import Scan


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "legacy.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(self.path).replace("\\", "/")}

    def tearDown(self):
        self.temp.cleanup()

    def legacy_database(self, collision=False):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.executescript("""
                CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT);
                INSERT INTO user VALUES (1, 'old-local-user');
                CREATE TABLE scan (
                    id VARCHAR(36) PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES user(id),
                    target VARCHAR(2048) NOT NULL, tools_json TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL, created_at FLOAT NOT NULL,
                    started_at FLOAT, finished_at FLOAT, current_tool VARCHAR(20),
                    completed_tools INTEGER NOT NULL, result_json TEXT, error VARCHAR(512)
                );
                INSERT INTO scan VALUES (
                    '11111111-1111-4111-8111-111111111111', 1, '127.0.0.1', '["nmap"]',
                    'finished', 100, 101, 102, NULL, 1, '{"findings":[]}', NULL
                );
            """)
            if collision:
                connection.execute("CREATE TABLE scan_legacy_auth (sentinel TEXT)")
                connection.execute("INSERT INTO scan_legacy_auth VALUES ('keep me')")

    def test_fresh_database_has_no_user_model(self):
        app = create_app(self.config)
        with app.app_context():
            self.assertEqual(inspect(db.engine).get_table_names(), ["scan"])
            self.assertNotIn("user_id", {column["name"] for column in inspect(db.engine).get_columns("scan")})
            db.engine.dispose()

    def test_migration_preserves_rows_archives_and_is_idempotent(self):
        self.legacy_database()
        for _ in range(2):
            app = create_app(self.config)
            with app.app_context():
                scan = db.session.get(Scan, "11111111-1111-4111-8111-111111111111")
                self.assertEqual(scan.target, "127.0.0.1")
                self.assertEqual(scan.result_json, '{"findings":[]}')
                self.assertEqual(scan.finished_at, 102)
                self.assertEqual(Scan.query.count(), 1)
                self.assertNotIn("user_id", {column["name"] for column in inspect(db.engine).get_columns("scan")})
                db.session.remove()
                db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM scan_legacy_auth").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT username FROM user").fetchone()[0], "old-local-user")

    def test_collision_leaves_existing_tables_intact(self):
        self.legacy_database(collision=True)
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            create_app(self.config)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT user_id FROM scan").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT sentinel FROM scan_legacy_auth").fetchone()[0], "keep me")

    def test_missing_columns_are_not_silently_replaced_by_sqlite_string_literals(self):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("CREATE TABLE scan (id TEXT, user_id INTEGER)")
            connection.execute("INSERT INTO scan VALUES ('preserve-me', 1)")
        with self.assertRaisesRegex(RuntimeError, "columns missing"):
            create_app(self.config)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT * FROM scan").fetchall(), [("preserve-me", 1)])
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='scan_legacy_auth'").fetchone())

    def test_copy_failure_rolls_back_rename(self):
        self.legacy_database()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("UPDATE scan SET id=NULL")
        with self.assertRaises(Exception):
            create_app(self.config)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("SELECT id, user_id FROM scan").fetchall(), [(None, 1)])
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='scan_legacy_auth'").fetchone())
