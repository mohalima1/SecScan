import unittest
from unittest.mock import patch
from app.services.sqlmap_service import parse_sqlmap_output, run_sqlmap_scan
from app.services.nikto_service import parse_nikto_output
from app.services.nmap_service import run_nmap_scan
from app.services.report_service import build_html_report, build_pdf_report


class AdapterTests(unittest.TestCase):
    def test_sqlmap_execution_failures_are_not_clean_assessments(self):
        for output in ("[CRITICAL] unable to connect to the target URL", "[CRITICAL] page not found (404)"):
            with self.subTest(output=output), patch("app.services.sqlmap_service.run_command", return_value={"status": "completed", "stdout": output, "stderr": "", "exit_code": 0}):
                result = run_sqlmap_scan("test", "http://localhost/a?id=1")
                self.assertEqual(result["status"], "error")
                self.assertEqual(result["findings"], [])

    def test_sqlmap_valid_negative_and_inconclusive_output_are_distinct(self):
        for output, expected in (("[CRITICAL] all tested parameters do not appear to be injectable", "completed"), ("sqlmap started but produced no assessment summary", "partial")):
            with self.subTest(output=output), patch("app.services.sqlmap_service.run_command", return_value={"status": "completed", "stdout": output, "stderr": "", "exit_code": 0}):
                self.assertEqual(run_sqlmap_scan("test", "http://localhost/a?id=1")["status"], expected)

    def test_sqlmap_heuristic_and_negative_output_are_not_findings(self):
        for output in ("GET parameter 'id' appears to be injectable", "all tested parameters do not appear to be injectable", "page not found (404)"):
            self.assertEqual(parse_sqlmap_output(output, "http://localhost/a?id=1"), [])

    def test_sqlmap_final_summary_keeps_parameter(self):
        output = "sqlmap identified the following injection point(s):\n---\nParameter: id (GET)\n    Type: boolean-based blind\n    Title: AND boolean-based blind\n    Payload: id=1 AND 1=1\n---"
        findings = parse_sqlmap_output(output, "http://localhost/a?id=1")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["parameter"], "id")

    def test_nikto_headers_preserve_affected_path(self):
        findings = parse_nikto_output("+ Target IP: 127.0.0.1\n+ /login: The anti-clickjacking X-Frame-Options header is not present.\n+ 1 host(s) tested", "http://localhost:8081/")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["url"], "http://localhost:8081/login")

    def test_nmap_services_are_observations(self):
        xml = '<nmaprun><host><address addr="127.0.0.1"/><ports><port portid="22" protocol="tcp"><state state="open"/><service name="ssh"/></port></ports></host></nmaprun>'
        with patch("app.services.nmap_service.run_command", return_value={"status": "completed", "stdout": xml, "stderr": "", "exit_code": 0}):
            result = run_nmap_scan("test", "127.0.0.1")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["observations"][0]["port"], 22)

    def test_reports_escape_untrusted_evidence_and_return_pdf_bytes(self):
        result = {"target": "<script>alert(1)</script>", "findings": [], "tool_results": {}, "observations": []}
        html = build_html_report(result)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertTrue(build_pdf_report(result).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
