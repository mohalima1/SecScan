import re
import time
from urllib.parse import urlsplit
import requests
from flask import current_app


def _zap_get(session, path, params=None, timeout=15):
    params = dict(params or {})
    key = current_app.config.get("ZAP_API_KEY", "")
    if key:
        params["apikey"] = key
    response = session.get(current_app.config["ZAP_API"] + path, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "code" in data:
        raise RuntimeError("ZAP rejected the API request. Check its API key and configuration.")
    return data


def _wait(session, kind, scan_id, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = _zap_get(session, f"/JSON/{kind}/view/status/", {"scanId": scan_id})
        if int(data.get("status", 0)) >= 100:
            return True
        time.sleep(2)
    return False


def run_zap_scan(scan_id, target, spider_timeout=120, active_timeout=300):
    session = requests.Session()
    spider_id = active_id = None
    completed = False
    try:
        _zap_get(session, "/JSON/core/view/version/")
        # A dedicated ZAP daemon and one backend worker prevent shared-session result leakage.
        _zap_get(session, "/JSON/core/action/newSession/", {"name": "", "overwrite": "true"})
        parsed = urlsplit(target)
        host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
        default_port = 443 if parsed.scheme == "https" else 80
        authority = host if parsed.port in (None, default_port) else f"{host}:{parsed.port}"
        origin = f"{parsed.scheme}://{authority}"
        context_name = "secscan-" + scan_id
        context = _zap_get(session, "/JSON/context/action/newContext/", {"contextName": context_name})
        context_id = context["contextId"]
        _zap_get(session, "/JSON/context/action/includeInContext/", {"contextName": context_name, "regex": "^" + re.escape(origin) + r"(?:/.*)?$"})
        _zap_get(session, "/JSON/context/action/setContextInScope/", {"contextName": context_name, "booleanInScope": "true"})
        spider = _zap_get(session, "/JSON/spider/action/scan/", {"url": target, "contextName": context_name, "recurse": "true", "maxChildren": "10"})
        spider_id = spider["scan"]
        spider_done = _wait(session, "spider", spider_id, spider_timeout)
        if not spider_done:
            return {"status": "timeout", "error": "ZAP spider exceeded its time limit.", "findings": [], "observations": []}
        active = _zap_get(session, "/JSON/ascan/action/scan/", {"url": target, "contextId": context_id, "inScopeOnly": "true", "recurse": "true"})
        active_id = active["scan"]
        active_done = _wait(session, "ascan", active_id, active_timeout)
        # Wait for passive analysis rather than an arbitrary sleep.
        passive_deadline = time.monotonic() + 60
        while time.monotonic() < passive_deadline:
            pending = _zap_get(session, "/JSON/pscan/view/recordsToScan/")
            if int(pending.get("recordsToScan", 0)) == 0:
                break
            time.sleep(2)
        else:
            active_done = False
        alerts = _zap_get(session, "/JSON/core/view/alerts/", {"baseurl": origin, "start": 0, "count": 9999}).get("alerts", [])
        findings, observations = [], []
        for alert in alerts:
            risk = str(alert.get("risk", "")).lower()
            record = {
                "tool": "zap", "title": alert.get("name") or alert.get("alert") or "ZAP reported issue",
                "severity": risk if risk in ("high", "medium", "low") else "info",
                "url": alert.get("url", ""), "parameter": alert.get("param", ""),
                "description": alert.get("description", ""), "evidence": alert.get("evidence") or alert.get("other") or "",
                "recommendation": alert.get("solution", ""), "source_confidence": alert.get("confidence", ""),
                "scanner_rule_id": alert.get("pluginId"), "cwe_id": alert.get("cweid"),
            }
            if record["severity"] == "info":
                observations.append(record)
            else:
                findings.append(record)
        completed = active_done
        return {"status": "completed" if completed else "partial", "error": None if completed else "ZAP reached its time limit; coverage is incomplete.", "findings": findings, "observations": observations}
    except (requests.RequestException, ValueError, KeyError, RuntimeError):
        current_app.logger.exception("ZAP scan failed")
        return {"status": "error", "error": "ZAP could not complete. Check its daemon, API key and backend logs.", "findings": [], "observations": []}
    finally:
        for kind, external_id in (("spider", spider_id), ("ascan", active_id)):
            if external_id is not None:
                try:
                    _zap_get(session, f"/JSON/{kind}/action/stop/", {"scanId": external_id})
                except Exception:
                    current_app.logger.warning("Could not stop ZAP %s job %s", kind, external_id)
        session.close()
