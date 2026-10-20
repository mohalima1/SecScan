import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app, db
from app.models.scan import Scan


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(self.temp.name) / "test.db").replace("\\", "/"),
            "ALLOWED_SCAN_HOSTS": ["127.0.0.1", "localhost", "::1"],
        })
        self.client = self.app.test_client()
        self.payload = {"target": "127.0.0.1", "tools": ["nmap"]}
        self.tools_patch = patch("app.routes.api.get_tool_status", return_value={"nmap": {"available": True}})
        self.tools_patch.start()

    def tearDown(self):
        self.tools_patch.stop()
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp.cleanup()

    def test_no_account_or_session_required(self):
        for route in ("/api/health", "/api/scans", "/api/tools/status"):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("Set-Cookie", response.headers)
        self.assertEqual(self.client.get("/api/auth/session").status_code, 404)
        with patch("app.services.scan_manager.Thread"):
            response = self.client.post("/api/scan/start", json=self.payload)
            self.assertEqual(response.status_code, 202)
            self.assertNotIn("Set-Cookie", response.headers)

    def test_untrusted_browser_cannot_start_scan(self):
        for headers in (
            {"Origin": "https://other.example"},
            {"Origin": "null"},
            {"Sec-Fetch-Site": "cross-site"},
        ):
            self.assertEqual(self.client.post("/api/scan/start", json=self.payload, headers=headers).status_code, 403)
        self.assertEqual(self.client.post("/api/scan/start", data=json.dumps(self.payload), content_type="text/plain").status_code, 415)
        self.assertEqual(self.client.get("/api/scans", headers={"Host": "attacker.example"}).status_code, 400)
        self.assertEqual(self.client.get("/api/scans").get_json()["scans"], [])

    def test_local_frontend_origin_can_start_scan(self):
        with patch("app.services.scan_manager.Thread"):
            response = self.client.post("/api/scan/start", json=self.payload, headers={"Origin": "http://127.0.0.1:8080"})
        self.assertEqual(response.status_code, 202)

    def test_malformed_request_and_out_of_scope_targets_are_rejected(self):
        for payload in ([], {"target": ["127.0.0.1"], "tools": ["nmap"]},
                        {"target": "http://example.test", "tools": ["zap"]},
                        {"target": "-iL", "tools": ["nmap"]},
                        {"target": "127.0.0.1", "tools": []},
                        {"target": "127.0.0.1", "tools": ["hydra"]},
                        {"target": "127.0.0.1", "tools": "nmap"},
                        {"target": "127.0.0.1", "tools": ["zap"]}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/scan/start", json=payload).status_code, 400)

    def test_missing_tools_are_rejected_before_job_creation(self):
        with patch("app.routes.api.get_tool_status", return_value={"nmap": {"available": False}}):
            response = self.client.post("/api/scan/start", json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("nmap", response.get_json()["error"])
        self.assertEqual(self.client.get("/api/scans").get_json()["scans"], [])

    def test_history_status_results_and_reports_are_local(self):
        scan_id = "11111111-1111-4111-8111-111111111111"
        sample = json.loads((Path(__file__).resolve().parents[2] / "docs/examples/report.json").read_text(encoding="utf-8"))
        sample["scan_id"] = scan_id
        with self.app.app_context():
            db.session.add(Scan(id=scan_id, target="127.0.0.1", tools_json='["nmap"]', status="finished", result_json=json.dumps(sample)))
            db.session.commit()
        other = self.app.test_client()
        self.assertEqual(len(other.get("/api/scans").get_json()["scans"]), 1)
        for suffix in ("status", "results", "report?format=html", "report?format=pdf"):
            self.assertEqual(other.get(f"/api/scan/{scan_id}/{suffix}").status_code, 200)
        self.assertEqual(other.get(f"/api/scan/{scan_id}/report?format=exe").status_code, 400)
        self.assertEqual(other.get("/api/scan/invalid/status").status_code, 404)

    def test_accepted_job_survives_request_and_capacity_is_bounded(self):
        with patch("app.services.scan_manager.Thread"):
            first = self.client.post("/api/scan/start", json=self.payload)
            self.assertEqual(first.status_code, 202)
            scan_id = first.get_json()["scan_id"]
            self.assertEqual(self.client.get(f"/api/scan/{scan_id}/status").get_json()["status"], "queued")
            self.assertEqual(self.client.get(f"/api/scan/{scan_id}/results").status_code, 202)
            self.assertEqual(self.client.get(f"/api/scan/{scan_id}/report").status_code, 409)
            self.assertEqual(self.client.post("/api/scan/start", json=self.payload).status_code, 429)


if __name__ == "__main__":
    unittest.main()
