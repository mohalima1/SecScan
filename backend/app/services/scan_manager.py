import json
import time
import uuid
from threading import BoundedSemaphore, Thread
from app import db
from app.models.scan import Scan
from app.services.tool_runner import run_scan


class ScanCapacityError(Exception):
    pass


class ScanManager:
    def __init__(self, app):
        self.app = app
        self.slots = BoundedSemaphore(app.config["MAX_CONCURRENT_SCANS"])

    def start(self, target, tools):
        if not self.slots.acquire(blocking=False):
            raise ScanCapacityError("A scan is already running. Wait for it to finish.")
        scan_id = str(uuid.uuid4())
        try:
            scan = Scan(id=scan_id, target=target, tools_json=json.dumps(tools), status="queued")
            db.session.add(scan)
            db.session.commit()
            Thread(target=self._worker, args=(scan_id, target, tools), daemon=True).start()
        except Exception:
            db.session.rollback()
            scan = db.session.get(Scan, scan_id)
            if scan:
                scan.status = "error"
                scan.error = "The scan worker could not start."
                scan.finished_at = time.time()
                db.session.commit()
            self.slots.release()
            raise
        return scan_id

    def _worker(self, scan_id, target, tools):
        with self.app.app_context():
            try:
                scan = db.session.get(Scan, scan_id)
                scan.status, scan.started_at = "running", time.time()
                db.session.commit()

                def progress(tool, completed):
                    scan = db.session.get(Scan, scan_id)
                    scan.current_tool, scan.completed_tools = tool, completed
                    db.session.commit()

                result = run_scan(target, tools, scan_id, on_progress=progress)
                scan = db.session.get(Scan, scan_id)
                scan.finished_at = time.time()
                result["started_at"], result["finished_at"] = scan.started_at, scan.finished_at
                result["duration_seconds"] = int(scan.finished_at - scan.started_at)
                scan.result_json = json.dumps(result, ensure_ascii=False)
                scan.status = "error" if result["outcome"] == "error" else "finished"
                scan.error = "All selected tools failed. Review their execution status." if scan.status == "error" else None
                scan.current_tool = None
                db.session.commit()
            except Exception:
                db.session.rollback()
                self.app.logger.exception("Scan worker failed for %s", scan_id)
                scan = db.session.get(Scan, scan_id)
                if scan:
                    scan.status, scan.finished_at = "error", time.time()
                    scan.error = "The scan could not be completed. Check the backend logs."
                    scan.current_tool = None
                    db.session.commit()
            finally:
                db.session.remove()
                self.slots.release()
