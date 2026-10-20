import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from app import create_app, db
from app.models.scan import Scan
from app.services.zap_service import run_zap_scan


class JobTests(unittest.TestCase):
    def test_worker_persists_results_and_releases_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(directory) / "jobs.db").replace("\\", "/")}
            app = create_app(config)
            with app.app_context():
                scan = Scan(id="22222222-2222-4222-8222-222222222222", target="127.0.0.1", tools_json='["nmap"]', status="queued")
                db.session.add(scan)
                db.session.commit()
            manager = app.extensions["scan_manager"]
            manager.slots.acquire()
            outcome = {"outcome": "completed", "findings": [], "observations": [], "tool_results": {"nmap": {"status": "completed"}}}
            with patch("app.services.scan_manager.run_scan", return_value=outcome):
                manager._worker("22222222-2222-4222-8222-222222222222", "127.0.0.1", ["nmap"])
            with app.app_context():
                scan = db.session.get(Scan, "22222222-2222-4222-8222-222222222222")
                self.assertEqual(scan.status, "finished")
                self.assertEqual(json.loads(scan.result_json)["outcome"], "completed")
                self.assertIsNotNone(scan.finished_at)
                db.session.remove()
                db.engine.dispose()
            self.assertTrue(manager.slots.acquire(blocking=False))
            manager.slots.release()

    def test_restart_stops_elapsed_clock_and_marks_interruption(self):
        with tempfile.TemporaryDirectory() as directory:
            config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(directory) / "restart.db").replace("\\", "/")}
            app = create_app(config)
            with app.app_context():
                db.session.add(Scan(id="33333333-3333-4333-8333-333333333333", target="127.0.0.1", tools_json='["nmap"]', status="running", started_at=time.time() - 20, current_tool="nmap"))
                db.session.commit()
                db.session.remove()
                db.engine.dispose()
            restarted = create_app(config)
            with restarted.app_context():
                scan = db.session.get(Scan, "33333333-3333-4333-8333-333333333333")
                self.assertEqual(scan.status, "error")
                self.assertIsNotNone(scan.finished_at)
                self.assertIsNone(scan.current_tool)
                self.assertIn("restarted", scan.error)
                db.session.remove()
                db.engine.dispose()


class ZapLifecycleTests(unittest.TestCase):
    def test_timed_out_spider_is_stopped(self):
        app = Flask(__name__)
        app.config.update(ZAP_API="http://127.0.0.1:8090", ZAP_API_KEY="test")
        calls = []

        def fake_api(session, path, params=None, timeout=15):
            calls.append((path, params))
            if path.endswith("newContext/"):
                return {"contextId": "1"}
            if path == "/JSON/spider/action/scan/":
                return {"scan": "42"}
            return {"Result": "OK"}

        with app.app_context(), patch("app.services.zap_service._zap_get", side_effect=fake_api):
            result = run_zap_scan("test", "http://127.0.0.1/", spider_timeout=0)
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["findings"], [])
        self.assertIn(("/JSON/spider/action/stop/", {"scanId": "42"}), calls)


if __name__ == "__main__":
    unittest.main()
