"""Availability checks shared by discovery and scan submission."""
import requests
from flask import current_app
from app.services.command import tool_command


def get_tool_status(selected=None):
    selected = selected or ("nmap", "sqlmap", "nikto", "zap")
    tools = {
        tool: {"available": bool(tool_command(tool))}
        for tool in selected if tool != "zap"
    }
    if "zap" in selected:
        try:
            key = current_app.config["ZAP_API_KEY"]
            response = requests.get(
                current_app.config["ZAP_API"] + "/JSON/core/view/version/",
                params={"apikey": key} if key else {},
                timeout=3,
            )
            response.raise_for_status()
            data = response.json()
            version = data.get("version") if isinstance(data, dict) else None
            tools["zap"] = {"available": bool(version), "version": version}
        except (requests.RequestException, ValueError):
            tools["zap"] = {"available": False}
    return tools
