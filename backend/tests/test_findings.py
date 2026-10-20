import unittest
from app.services.findings_processor import process_findings


class FindingTests(unittest.TestCase):
    def test_matching_header_findings_keep_both_tools_and_evidence(self):
        findings = [
            {"tool": "OWASP ZAP", "title": "Missing Anti-clickjacking Header", "severity": "medium", "url": "https://example.test/a", "evidence": "ZAP evidence"},
            {"tool": "Nikto", "title": "Missing Anti-Clickjacking Header", "severity": "low", "url": "https://example.test/a", "evidence": "Nikto evidence"},
        ]
        result = process_findings(findings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tools"], ["nikto", "zap"])
        self.assertEqual(result[0]["severity"], "medium")
        self.assertEqual(result[0]["confidence"], "corroborated")
        self.assertEqual(len(result[0]["sources"]), 2)
        self.assertEqual(result[0]["status"], "reported")

    def test_different_endpoints_and_parameters_are_not_merged(self):
        findings = [
            {"tool": "zap", "title": "SQL Injection", "severity": "high", "url": "https://example.test/a", "parameter": "id"},
            {"tool": "SQLMap", "title": "SQL Injection", "severity": "high", "url": "https://example.test/b", "parameter": "id"},
            {"tool": "SQLMap", "title": "SQL Injection", "severity": "high", "url": "https://example.test/a", "parameter": "name"},
        ]
        self.assertEqual(len(process_findings(findings)), 3)

    def test_missing_locations_are_not_cross_correlated(self):
        result = process_findings([
            {"tool": "zap", "title": "SQL Injection", "severity": "high"},
            {"tool": "SQLMap", "title": "SQL Injection", "severity": "critical"},
        ])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(f["confidence"] == "single-tool" for f in result))

    def test_unknown_severity_is_normalized(self):
        result = process_findings([{"tool": "nikto", "title": "Issue", "severity": "UNKNOWN"}])
        self.assertEqual(result[0]["severity"], "info")

    def test_csp_misconfiguration_is_not_a_missing_csp_header(self):
        result = process_findings([
            {"tool": "zap", "title": "Content Security Policy (CSP) Misconfiguration", "url": "https://example.test/", "severity": "medium"},
            {"tool": "nikto", "title": "Missing Content-Security-Policy Header", "url": "https://example.test/", "severity": "low"},
        ])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(f["confidence"] == "single-tool" for f in result))


if __name__ == "__main__":
    unittest.main()
