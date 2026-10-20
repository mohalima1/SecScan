import os
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

db = SQLAlchemy()


def create_app(test_config=None):
    if test_config is None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///mini_cybersec.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=16384,
        ALLOWED_SCAN_HOSTS=[h.strip().lower() for h in os.environ.get("ALLOWED_SCAN_HOSTS", "localhost,127.0.0.1,::1").split(",") if h.strip()],
        ZAP_API=os.environ.get("ZAP_API", "http://127.0.0.1:8090").rstrip("/"),
        ZAP_API_KEY=os.environ.get("ZAP_API_KEY", ""),
        NMAP_PATH=os.environ.get("NMAP_PATH", ""),
        SQLMAP_PATH=os.environ.get("SQLMAP_PATH", ""),
        NIKTO_PATH=os.environ.get("NIKTO_PATH", ""),
        PERL_PATH=os.environ.get("PERL_PATH", ""),
        MAX_CONCURRENT_SCANS=1,
        TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"],
        FRONTEND_ORIGINS=[origin.strip() for origin in os.environ.get(
            "FRONTEND_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
        ).split(",") if origin.strip()],
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}})
    db.init_app(app)
    from app.models import Scan
    from app.storage import initialize_storage
    from app.routes.api import api_bp
    from app.services.scan_manager import ScanManager
    app.register_blueprint(api_bp, url_prefix="/api")
    with app.app_context():
        try:
            initialize_storage()
        except Exception:
            db.engine.dispose()
            raise
        for scan in Scan.query.filter(Scan.status.in_(["queued", "running"])).all():
            scan.status = "error"
            scan.finished_at = time.time()
            scan.current_tool = None
            scan.error = "The backend restarted before this scan finished. Start a new scan."
        db.session.commit()
    app.extensions["scan_manager"] = ScanManager(app)

    @app.before_request
    def guard_local_api():
        origin = request.headers.get("Origin")
        if origin and origin not in app.config["FRONTEND_ORIGINS"]:
            return jsonify(error="This browser origin is not allowed."), 403
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            return jsonify(error="Cross-site requests are not allowed."), 403
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not request.is_json:
            return jsonify(error="Send an application/json request."), 415

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unhandled API error")
        db.session.rollback()
        return jsonify(error="The request could not be completed."), 500

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
    return app
