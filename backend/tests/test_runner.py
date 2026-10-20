import unittest
from unittest.mock import patch
from app.services.tool_runner import run_scan
from app.services.target_validation import validate_target


class RunnerTests(unittest.TestCase):
    def test_partial_scan_without_findings_still_has_partial_coverage(self):
        with patch("app.services.tool_runner.run_zap_scan", return_value={"status": "partial", "findings": [], "observations": []}):
            result = run_scan("http://127.0.0.1/", ["zap"], "test")
        self.assertEqual(result["outcome"], "partial")
        self.assertEqual(result["total_findings"], 0)

    def test_url_host_port_and_ipv6_are_parsed(self):
        self.assertEqual(validate_target("https://localhost:8443/a?id=1", ["nmap"], ["localhost"])["port"], 8443)
        self.assertEqual(validate_target("https://localhost:8443/a", ["nmap"], ["localhost"])["host"], "localhost")
        self.assertEqual(validate_target("http://[::1]:8081/", ["zap"], ["::1"])["host"], "::1")

    def test_failed_tool_does_not_abort_others_or_count_as_vulnerability(self):
        with patch("app.services.tool_runner.run_zap_scan", side_effect=RuntimeError("unavailable")), patch("app.services.tool_runner.run_nmap_scan", return_value={"status": "completed", "findings": [], "observations": [{"title": "Open port 80", "port": 80}]}):
            result = run_scan("http://127.0.0.1", ["zap", "nmap"], "test")
        self.assertEqual(result["outcome"], "partial")
        self.assertEqual(result["total_findings"], 0)
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual(result["tool_results"]["zap"]["status"], "error")
        self.assertEqual(result["tools_ran"], ["nmap"])

    def test_no_sqlmap_detection_does_not_confirm_zap(self):
        zap = {"status": "completed", "findings": [{"tool": "OWASP ZAP", "title": "SQL Injection", "severity": "high", "url": "http://127.0.0.1/a?id=1", "parameter": "id"}], "observations": []}
        sqlmap = {"status": "completed", "findings": [], "observations": [{"title": "No confirmed SQL injection"}]}
        with patch("app.services.tool_runner.run_zap_scan", return_value=zap), patch("app.services.tool_runner.run_sqlmap_scan", return_value=sqlmap):
            result = run_scan("http://127.0.0.1/a?id=1", ["zap", "sqlmap"], "test")
        self.assertEqual(result["total_findings"], 1)
        self.assertEqual(result["findings"][0]["confidence"], "single-tool")
        self.assertEqual(result["findings"][0]["status"], "reported")


if __name__ == "__main__":
    unittest.main()
