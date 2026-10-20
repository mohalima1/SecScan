import json
import time
from app import db


class Scan(db.Model):
    __tablename__ = "scan"

    id = db.Column(db.String(36), primary_key=True)
    target = db.Column(db.String(2048), nullable=False)
    tools_json = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="queued")
    created_at = db.Column(db.Float, nullable=False, default=time.time)
    started_at = db.Column(db.Float)
    finished_at = db.Column(db.Float)
    current_tool = db.Column(db.String(20))
    completed_tools = db.Column(db.Integer, nullable=False, default=0)
    result_json = db.Column(db.Text)
    error = db.Column(db.String(512))

    def summary(self):
        tools = json.loads(self.tools_json)
        elapsed = max(0, int((self.finished_at or time.time()) - self.started_at)) if self.started_at else 0
        return {
            "scan_id": self.id, "target": self.target, "tools": tools, "status": self.status,
            "created_at": self.created_at, "started_at": self.started_at, "finished_at": self.finished_at,
            "elapsed": elapsed, "current_tool": self.current_tool,
            "completed_tools": self.completed_tools, "total_tools": len(tools), "error": self.error,
        }
