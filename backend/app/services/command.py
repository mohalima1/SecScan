import subprocess
import shutil
import sys
from pathlib import Path

from flask import current_app, has_app_context


def tool_command(tool):
    """Resolve native executables or configured Python/Perl scanner scripts."""
    configured = current_app.config.get(f"{tool.upper()}_PATH") if has_app_context() else None
    candidate = configured or tool
    if configured and Path(configured).is_file():
        script = str(Path(configured).resolve())
        if tool == "sqlmap" and script.lower().endswith(".py"):
            return [sys.executable, script]
        if tool == "nikto" and script.lower().endswith(".pl"):
            perl = shutil.which(current_app.config.get("PERL_PATH") or "perl") if has_app_context() else shutil.which("perl")
            return [perl, script] if perl else None
    executable = shutil.which(candidate)
    return [executable] if executable else None


def run_command(command, timeout):
    if has_app_context() and command[0] in {"nmap", "sqlmap", "nikto"}:
        prefix = tool_command(command[0])
        if prefix is None:
            return {"status": "error", "error": f"{command[0]} is unavailable. Check PATH or its configured tool path.", "findings": [], "observations": []}
        command = prefix + command[1:]
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except FileNotFoundError:
        return {"status": "error", "error": f"{command[0]} is not installed or is not on PATH.", "findings": [], "observations": []}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": f"{command[0]} exceeded its {timeout}s time limit.", "findings": [], "observations": []}
    if process.returncode != 0:
        return {"status": "error", "exit_code": process.returncode, "error": (process.stderr or process.stdout or "The scanner exited unsuccessfully.")[-1000:], "findings": [], "observations": []}
    return {"status": "completed", "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}
