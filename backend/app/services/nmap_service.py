import xml.etree.ElementTree as ET
from app.services.command import run_command


def run_nmap_scan(scan_id, host, port=None, timeout_sec=180):
    command = ["nmap", "-Pn", "-sT", "-sV", "--version-light", "-T3"]
    if ":" in host:
        command.append("-6")
    command.extend(["-p", str(port)] if port else ["--top-ports", "1000"])
    command.extend(["-oX", "-", "--", host])
    result = run_command(command, timeout_sec)
    if result["status"] != "completed":
        return result
    try:
        root = ET.fromstring(result.pop("stdout"))
        observations = []
        for host_element in root.findall("host"):
            address = host_element.find("address")
            address_value = address.get("addr", host) if address is not None else host
            for element in host_element.findall(".//port"):
                state, service = element.find("state"), element.find("service")
                if state is None or state.get("state") != "open":
                    continue
                observations.append({
                    "title": f'Open port {element.get("portid")}/{element.get("protocol")}',
                    "host": address_value, "port": int(element.get("portid")),
                    "protocol": element.get("protocol"),
                    "service": service.get("name", "unknown") if service is not None else "unknown",
                    "product": service.get("product", "") if service is not None else "",
                    "version": service.get("version", "") if service is not None else "",
                    "description": "An open service is an observation; it is not proof of a vulnerability.",
                })
    except (ET.ParseError, ValueError) as error:
        return {"status": "error", "error": f"Nmap returned invalid XML: {error}", "findings": [], "observations": []}
    return {"status": "completed", "exit_code": 0, "findings": [], "observations": observations}
