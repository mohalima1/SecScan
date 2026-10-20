import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

SEVERITIES = ["critical", "high", "medium", "low", "info"]
TOOL_IDS = {"owasp zap": "zap", "zap": "zap", "sqlmap": "sqlmap", "nmap": "nmap", "nikto": "nikto"}
ISSUE_TITLES = {
    "content security policy (csp) header not set": "missing-csp",
    "missing content-security-policy header": "missing-csp",
    "missing anti-clickjacking header": "missing-clickjacking-protection",
    "missing x-frame-options header": "missing-clickjacking-protection",
    "strict-transport-security header not set": "missing-hsts",
    "missing hsts header": "missing-hsts",
    "x-content-type-options header missing": "missing-content-type-options",
    "missing x-content-type-options header": "missing-content-type-options",
    "missing referrer-policy header": "missing-referrer-policy",
    "missing permissions-policy header": "missing-permissions-policy",
    "cookie without samesite attribute": "cookie-samesite",
    "cookie missing samesite attribute": "cookie-samesite",
    "cookie no httponly flag": "cookie-httponly",
    "cookie missing httponly flag": "cookie-httponly",
    "cookie without secure flag": "cookie-secure",
    "cookie missing secure flag": "cookie-secure",
    "sql injection": "sql-injection",
}


def canonical_url(value):
    if not value:
        return ""
    try:
        parsed = urlsplit(str(value))
        host = parsed.hostname or ""
        authority = f"[{host}]" if ":" in host else host
        if parsed.port and parsed.port != {"http": 80, "https": 443}.get(parsed.scheme):
            authority += f":{parsed.port}"
        return urlunsplit((parsed.scheme.lower(), authority.lower(), parsed.path or "/", parsed.query, ""))
    except ValueError:
        return str(value)


def process_findings(findings):
    groups = {}
    for index, item in enumerate(findings):
        source = dict(item)
        source["tool"] = TOOL_IDS.get(str(source.get("tool", "")).lower(), str(source.get("tool", "unknown")).lower())
        title = str(source.get("title") or "Reported issue")
        severity = str(source.get("severity") or "info").lower()
        source["severity"] = severity if severity in SEVERITIES else "info"
        source["url"] = canonical_url(source.get("url", ""))
        source["parameter"] = str(source.get("parameter") or "")
        issue_type = source.get("issue_type")
        if not issue_type:
            normalized = re.sub(r"\s+", " ", title.lower()).strip()
            issue_type = ISSUE_TITLES.get(normalized, normalized)
        source["issue_type"] = issue_type
        # No known location means there is no evidence that two reports concern the same issue.
        location = source["url"] or f"unknown-location-{index}"
        key = (issue_type, location, source["parameter"])
        group = groups.setdefault(key, {
            "id": hashlib.sha256(repr(key).encode()).hexdigest()[:16],
            "issue_type": issue_type, "title": title, "severity": source["severity"],
            "url": source["url"], "parameter": source["parameter"],
            "description": str(source.get("description") or ""),
            "recommendation": str(source.get("recommendation") or ""),
            "status": "reported", "sources": [],
        })
        group["sources"].append(source)
        if SEVERITIES.index(source["severity"]) < SEVERITIES.index(group["severity"]):
            group["severity"] = source["severity"]
        if not group["recommendation"]:
            group["recommendation"] = str(source.get("recommendation") or "")
    result = []
    for group in groups.values():
        group["tools"] = sorted({source["tool"] for source in group["sources"]})
        group["confidence"] = "corroborated" if len(group["tools"]) > 1 else "single-tool"
        group["occurrences"] = len(group["sources"])
        group["evidence"] = "\n\n".join(f'{source["tool"]}: {source.get("evidence", "")}' for source in group["sources"])
        result.append(group)
    return sorted(result, key=lambda f: (SEVERITIES.index(f["severity"]), f["title"], f["url"]))
