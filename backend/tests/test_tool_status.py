import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from app.services.command import run_command, tool_command
from app.services.tool_status import get_tool_status


class ToolResolutionTests(unittest.TestCase):
    def test_python_script_with_spaces_is_launched_without_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "scanner with spaces.py"
            script.write_text("import sys; print(sys.argv[1])", encoding="utf-8")
            app = Flask(__name__)
            app.config["SQLMAP_PATH"] = str(script)
            with app.app_context():
                self.assertEqual(tool_command("sqlmap"), [sys.executable, str(script.resolve())])
                result = run_command(["sqlmap", "literal & argument"], 10)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["stdout"].strip(), "literal & argument")

    def test_nikto_requires_perl_even_when_script_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "nikto.pl"
            script.write_text("", encoding="utf-8")
            app = Flask(__name__)
            app.config["NIKTO_PATH"] = str(script)
            with app.app_context(), patch("app.services.command.shutil.which", return_value=None):
                self.assertEqual(get_tool_status(["nikto"]), {"nikto": {"available": False}})
                self.assertEqual(run_command(["nikto", "-h", "http://127.0.0.1"], 1)["status"], "error")

    def test_invalid_configured_path_does_not_fall_back_to_another_scanner(self):
        app = Flask(__name__)
        app.config["NMAP_PATH"] = "missing/installation/nmap"
        with app.app_context(), patch("app.services.command.shutil.which", return_value=None):
            self.assertEqual(get_tool_status(["nmap"]), {"nmap": {"available": False}})

    def test_nikto_uses_configured_perl_without_requiring_updated_path(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "nikto.pl"
            script.write_text("", encoding="utf-8")
            app = Flask(__name__)
            app.config.update(NIKTO_PATH=str(script), PERL_PATH="C:/Strawberry/perl/bin/perl.exe")
            def locate(candidate):
                return candidate if candidate == "C:/Strawberry/perl/bin/perl.exe" else None
            with app.app_context(), patch("app.services.command.shutil.which", side_effect=locate):
                self.assertEqual(tool_command("nikto"), ["C:/Strawberry/perl/bin/perl.exe", str(script.resolve())])

    def test_timeout_is_an_explicit_failure(self):
        with patch("app.services.command.subprocess.run", side_effect=subprocess.TimeoutExpired(["nmap"], 1)):
            self.assertEqual(run_command(["nmap"], 1)["status"], "timeout")

    def test_unexpected_zap_response_is_unavailable(self):
        app = Flask(__name__)
        app.config.update(ZAP_API="http://127.0.0.1:8090", ZAP_API_KEY="")
        with app.app_context(), patch("app.services.tool_status.requests.get") as get:
            get.return_value.json.return_value = ["not", "a", "version"]
            self.assertFalse(get_tool_status(["zap"])["zap"]["available"])
