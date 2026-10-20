import json
import uuid
from flask import Blueprint, current_app, jsonify, request, Response
from app.services.tool_status import get_tool_status
from app.models.scan import Scan
from app.services.scan_manager import ScanCapacityError
from app.services.target_validation import validate_target
from app.services.report_service import build_html_report, build_pdf_report

api_bp = Blueprint("api", __name__)


def find_scan(scan_id):
    try:
        canonical_id = str(uuid.UUID(scan_id))
    except ValueError:
        return None
    return Scan.query.filter_by(id=canonical_id).first()


@api_bp.get("/health")
def health():
    return jsonify(status="ok", service="secscan")


@api_bp.post("/scan")
@api_bp.post("/scan/start")
def scan_start():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send a JSON object."), 400
    tools = data.get("tools")
    try:
        target = validate_target(data.get("target"), tools, current_app.config["ALLOWED_SCAN_HOSTS"])
    except ValueError as error:
        return jsonify(error=str(error)), 400
    unavailable = [name for name, state in get_tool_status(tools).items() if not state["available"]]
    if unavailable:
        return jsonify(error="Install or start these tools before scanning: " + ", ".join(unavailable)), 503
    try:
        scan_id = current_app.extensions["scan_manager"].start(target["target"], tools)
    except ScanCapacityError as error:
        return jsonify(error=str(error)), 429, {"Retry-After": "5"}
    return jsonify(scan_id=scan_id, status="queued", target=target["target"], tools=tools), 202


@api_bp.get("/scans")
def scan_history():
    scans = Scan.query.order_by(Scan.created_at.desc()).limit(50).all()
    return jsonify(scans=[scan.summary() for scan in scans])


@api_bp.get("/scan/<scan_id>/status")
def scan_status(scan_id):
    scan = find_scan(scan_id)
    if not scan:
        return jsonify(error="Scan not found."), 404
    return jsonify(scan.summary())


@api_bp.get("/scan/<scan_id>/results")
def scan_results(scan_id):
    scan = find_scan(scan_id)
    if not scan:
        return jsonify(error="Scan not found."), 404
    if scan.status in ("queued", "running"):
        return jsonify(scan.summary()), 202
    if scan.result_json:
        return jsonify(json.loads(scan.result_json))
    return jsonify(error=scan.error or "No scan results are available.", status=scan.status), 409


@api_bp.get("/scan/<scan_id>/report")
def scan_report(scan_id):
    scan = find_scan(scan_id)
    if not scan:
        return jsonify(error="Scan not found."), 404
    if not scan.result_json:
        return jsonify(error="The scan has no completed report yet."), 409
    fmt = request.args.get("format", "pdf").lower()
    if fmt not in ("pdf", "html"):
        return jsonify(error="Choose pdf or html report format."), 400
    result = json.loads(scan.result_json)
    if fmt == "html":
        response = Response(build_html_report(result), mimetype="text/html")
        response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"
    else:
        response = Response(build_pdf_report(result), mimetype="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="secscan-{scan.id}.{fmt}"'
    return response


@api_bp.get("/tools/status")
def tools_status():
    return jsonify(tools=get_tool_status(), allowed_hosts=current_app.config["ALLOWED_SCAN_HOSTS"])
