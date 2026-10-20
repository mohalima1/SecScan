import logging
from datetime import datetime, timezone
from urllib.parse import urlsplit
from app.services.findings_processor import process_findings, SEVERITIES
from app.services.zap_service import run_zap_scan
from app.services.nmap_service import run_nmap_scan
from app.services.sqlmap_service import run_sqlmap_scan
from app.services.nikto_service import run_nikto_scan

logger = logging.getLogger(__name__)


def run_scan(target: str, tools: list, scan_id: str, on_progress=None):
    adapters = {"zap": run_zap_scan, "nmap": run_nmap_scan, "sqlmap": run_sqlmap_scan, "nikto": run_nikto_scan}
    if not tools or any(tool not in adapters for tool in tools):
        raise ValueError("Unsupported scan tools")
    tool_results, raw_findings, observations = {}, [], []
    parsed = urlsplit(target if "://" in target else ("http://[" + target + "]" if target.count(":") > 1 and not target.startswith("[") else "http://" + target))
    for index, tool in enumerate(tools):
        if on_progress:
            on_progress(tool, index)
        try:
            if tool == "nmap":
                nmap_port = parsed.port or (443 if parsed.scheme == "https" else (80 if parsed.scheme == "http" else None))
                output = adapters[tool](scan_id, parsed.hostname, port=nmap_port)
            else:
                output = adapters[tool](scan_id, target)
            if not isinstance(output, dict) or output.get("status") not in {"completed", "error", "timeout", "partial"}:
                raise ValueError("Invalid adapter response")
        except Exception:
            logger.exception("Scanner %s failed for scan %s", tool, scan_id)
            output = {"status": "error", "error": f"{tool} could not run. Check installation and backend logs.", "findings": [], "observations": []}
        findings = output.get("findings", [])
        raw_findings.extend(dict(finding, tool=tool) for finding in findings)
        observations.extend(dict(observation, tool=tool) for observation in output.get("observations", []))
        tool_results[tool] = {key: value for key, value in output.items() if key not in ("findings", "observations")}
        tool_results[tool]["finding_count"] = len(findings)
        if on_progress:
            on_progress(None, index + 1)
    findings = process_findings(raw_findings)
    successful = [tool for tool in tools if tool_results[tool]["status"] == "completed"]
    partial = any(meta["status"] == "partial" for meta in tool_results.values())
    outcome = "completed" if len(successful) == len(tools) else ("partial" if successful or raw_findings or partial else "error")
    return {
        "scan_id": scan_id, "target": target, "timestamp": datetime.now(timezone.utc).isoformat(),
        "tools_selected": tools, "tools_ran": successful, "tool_results": tool_results,
        "outcome": outcome, "raw_finding_count": len(raw_findings), "total_findings": len(findings),
        "counts": {severity: sum(f["severity"] == severity for f in findings) for severity in SEVERITIES},
        "findings": findings, "observations": observations,
    }
