import re
from urllib.parse import urljoin
from app.services.command import run_command

RULES = [
    ("strict-transport-security", "Missing HSTS Header", "missing-hsts"),
    ("x-content-type-options", "Missing X-Content-Type-Options Header", "missing-content-type-options"),
    ("x-frame-options", "Missing Anti-Clickjacking Header", "missing-clickjacking-protection"),
    ("content-security-policy", "Missing Content-Security-Policy Header", "missing-csp"),
    ("referrer-policy", "Missing Referrer-Policy Header", "missing-referrer-policy"),
    ("permissions-policy", "Missing Permissions-Policy Header", "missing-permissions-policy"),
]
IGNORED = ("target ip:", "target hostname:", "target port:", "start time:", "end time:", "server:", "requests:", "host(s) tested", "no cgi directories", "entries checked", "scan terminated", "error limit", "your nikto", "ssl info:")


def parse_nikto_output(output, target):
    findings, seen = [], set()
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("+"):
            continue
        description = line.lstrip("+ ").strip()
        lower = description.lower()
        if not description or any(value in lower for value in IGNORED):
            continue
        # Only parse issue-shaped lines; banners and scan summaries are not issues.
        path_match = re.match(r"(/[^\s:]*):\s*(.+)", description)
        if not path_match:
            continue
        path, details = path_match.groups()
        url = urljoin(target, path)
        title, issue_type = details[:120], None
        for marker, rule_title, rule_type in RULES:
            if marker in details.lower() and any(word in details.lower() for word in ("not", "missing", "absent")):
                title, issue_type = rule_title, rule_type
                break
        key = (url, details)
        if key in seen:
            continue
        seen.add(key)
        finding = {"tool": "nikto", "title": title, "severity": "low", "url": url,
                   "parameter": "", "description": details, "evidence": line,
                   "source_confidence": "scanner-reported",
                   "recommendation": "Verify the response and apply the relevant server configuration fix."}
        if issue_type:
            finding["issue_type"] = issue_type
        findings.append(finding)
    return findings


def run_nikto_scan(scan_id, target, timeout_sec=600):
    result = run_command(["nikto", "-h", target, "-ask", "no", "-nointeractive", "-maxtime", "540s"], timeout_sec)
    if result["status"] != "completed":
        return result
    output = result["stdout"] + "\n" + result.get("stderr", "")
    if re.search(r"(?:ERROR:|error limit reached|scan terminated)", output, re.I):
        return {"status": "error", "error": "Nikto reported a scan error. Check target reachability and backend logs.", "findings": parse_nikto_output(output, target), "observations": []}
    return {"status": "completed", "exit_code": 0, "findings": parse_nikto_output(output, target), "observations": []}
