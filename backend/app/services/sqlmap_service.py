import re
import tempfile
from app.services.command import run_command


def parse_sqlmap_output(output, url):
    # Confirmation requires the tool's final injection summary, not a heuristic log line.
    marker = re.search(r"identified the following injection point", output, re.I)
    if not marker:
        return []
    summary = output[marker.start():]
    findings = []
    for match in re.finditer(r"Parameter:\s*(.+?)\s*\((GET|POST|URI|Cookie|HEADER)\)(.*?)(?=\nParameter:|\Z)", summary, re.I | re.S):
        parameter, method, details = match.groups()
        if not re.search(r"Type:\s*\S", details):
            continue
        findings.append({
            "tool": "sqlmap", "title": "SQL Injection", "issue_type": "sql-injection",
            "severity": "high", "url": url, "parameter": parameter.strip(),
            "description": f"SQLMap reported an injection point in {method.upper()} parameter {parameter.strip()}.",
            "evidence": match.group(0).strip()[:4000],
            "source_confidence": "scanner-reported",
            "recommendation": "Use parameterized database queries and verify the reported injection point manually.",
        })
    return findings


def run_sqlmap_scan(scan_id, url, timeout_sec=300):
    command = ["sqlmap", "-u", url, "--batch", "--level", "1", "--risk", "1", "--timeout", "10", "--retries", "1", "--threads", "1", "--disable-coloring", "--ignore-redirects"]
    with tempfile.TemporaryDirectory(prefix="secscan-sqlmap-") as directory:
        result = run_command(command + ["--output-dir", directory], timeout_sec)
    if result["status"] != "completed":
        return result
    output = result["stdout"] + "\n" + result.get("stderr", "")
    findings = parse_sqlmap_output(output, url)
    negative = "all tested parameters do not appear to be injectable" in output.lower()
    fatal = any("[critical]" in line.lower() and "all tested parameters do not appear to be injectable" not in line.lower() for line in output.splitlines())
    if fatal:
        return {"status": "error", "error": "SQLMap reported a target or execution error. Check target reachability and parameters.", "findings": findings, "observations": []}
    if not findings and not negative:
        return {"status": "partial", "error": "SQLMap did not produce a conclusive assessment summary.", "findings": [], "observations": []}
    return {"status": "completed", "exit_code": 0, "findings": findings, "observations": []}
