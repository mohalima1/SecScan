import ipaddress
import re
from urllib.parse import urlsplit

SUPPORTED_TOOLS = {"zap", "nmap", "sqlmap", "nikto"}


def validate_target(value, tools, allowed_hosts):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("Enter a target URL or IP address (up to 2048 characters).")
    if not isinstance(tools, list) or not tools or any(not isinstance(t, str) or t not in SUPPORTED_TOOLS for t in tools):
        raise ValueError("Select one or more supported tools: zap, nmap, sqlmap, nikto.")
    if len(tools) != len(set(tools)):
        raise ValueError("Each tool may only be selected once.")
    target = value.strip()
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in target) or target.startswith("-") or "\\" in target:
        raise ValueError("The target contains invalid characters.")
    is_url = "://" in target
    try:
        if not is_url:
            try:
                ipaddress.ip_address(target)
                target_to_parse = f"http://[{target}]" if ":" in target else f"http://{target}"
            except ValueError:
                target_to_parse = f"http://{target}"
        else:
            target_to_parse = target
        parsed = urlsplit(target_to_parse)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError as error:
        raise ValueError("Enter a valid host and port (1-65535).") from error
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password or parsed.fragment or not host or port == 0:
        raise ValueError("Use an HTTP(S) URL without credentials or a fragment, or an IP address.")
    if not re.fullmatch(r"[a-z0-9.:-]+", host) or "%" in host:
        raise ValueError("Enter a valid hostname or IP address.")
    if not is_url:
        try:
            ipaddress.ip_address(host)
        except ValueError as error:
            raise ValueError("Use an HTTP(S) URL for hostnames, or enter a bare IP address.") from error
        if parsed.path not in ("", "/") or parsed.query:
            raise ValueError("Include http:// or https:// when specifying a path or query.")
    allowed_set = {str(h).lower().rstrip(".") for h in allowed_hosts}
    if "*" not in allowed_set and host not in allowed_set:
        raise ValueError("This host is outside the configured scan scope. Add the exact host to ALLOWED_SCAN_HOSTS.")
    if not is_url and any(tool != "nmap" for tool in tools):
        raise ValueError("Web scanners require a full http:// or https:// URL.")
    return {"target": target, "host": host, "port": port, "is_url": is_url}
