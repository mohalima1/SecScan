from html import escape
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def build_html_report(result):
    esc = lambda value: escape(str(value if value is not None else ""), quote=True)
    sections = []
    for finding in result.get("findings", []):
        sources = "".join(
            f'<h4>{esc(source.get("tool"))}</h4><pre>{esc(source.get("evidence"))}</pre>'
            for source in finding.get("sources", [])
        )
        sections.append(
            f'<section><h3>{esc(finding.get("title"))}</h3>'
            f'<p>{esc(finding.get("severity"))} | {esc(finding.get("confidence"))} | {esc(finding.get("status"))}</p>'
            f'<p>Location: {esc(finding.get("url"))} | Parameter: {esc(finding.get("parameter"))}</p>'
            f'<p>{esc(finding.get("description"))}</p>{sources}'
            f'<p>Remediation: {esc(finding.get("recommendation"))}</p></section>'
        )
    tools = "".join(f'<li>{esc(tool)}: {esc(meta.get("status"))} {esc(meta.get("error") or "")}</li>' for tool, meta in result.get("tool_results", {}).items())
    observations = "".join(f'<li>{esc(item.get("tool"))}: {esc(item.get("title"))} {esc(item.get("description") or "")}</li>' for item in result.get("observations", []))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>SecScan report</title><style>
body {{ font-family: sans-serif; line-height: 1.5; max-width: 960px; margin: 32px auto; padding: 20px; color: #18232d; }}
section {{ border-top: 1px solid #bac4ce; padding-block: 16px; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f1f4f6; padding: 12px; }}
p, li {{ overflow-wrap: anywhere; }}
</style></head><body><h1>SecScan assessment report</h1>
<p>Target: {esc(result.get("target"))}</p><p>Scan ID: {esc(result.get("scan_id"))}</p>
<p>Generated: {esc(result.get("timestamp"))}</p>
<p>Outcome: {esc(result.get("outcome"))} | Duration: {esc(result.get("duration_seconds"))}s</p>
<p>Unique reported issues: {esc(result.get("total_findings", 0))}</p>
<p>Automated findings require manual verification. A failed tool or empty result does not establish that the target is secure.</p>
<h2>Tool execution</h2><ul>{tools}</ul>
<h2>Reported issues</h2>{''.join(sections) or '<p>No issues were reported by the completed tools.</p>'}
<h2>Observations</h2><ul>{observations or '<li>No observations.</li>'}</ul></body></html>"""


def build_pdf_report(result):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=(8.5 * inch, 11 * inch), rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    styles["BodyText"].wordWrap = "CJK"
    styles["BodyText"].textColor = colors.HexColor("#18232d")
    story = []

    def paragraph(value, style="BodyText"):
        text = escape(str(value if value is not None else "")).replace("\n", "<br/>")
        story.append(Paragraph(text, styles[style]))
        story.append(Spacer(1, 7))

    paragraph("SecScan assessment report", "Title")
    for key in ("target", "scan_id", "timestamp", "outcome", "duration_seconds", "total_findings"):
        paragraph(f"{key.replace('_', ' ').title()}: {result.get(key, '')}")
    paragraph("Automated findings require manual verification. Failed tools and empty results do not establish that the target is secure.")
    paragraph("Tool execution", "Heading2")
    for tool, meta in result.get("tool_results", {}).items():
        paragraph(f"{tool}: {meta.get('status')} {meta.get('error') or ''}")
    paragraph("Reported issues", "Heading2")
    for finding in result.get("findings", []):
        paragraph(finding.get("title"), "Heading3")
        paragraph(f"{finding.get('severity')} | {finding.get('confidence')} | {finding.get('status')}")
        paragraph(f"Location: {finding.get('url')} | Parameter: {finding.get('parameter')}")
        paragraph(finding.get("description"))
        for source in finding.get("sources", []):
            paragraph(f"{source.get('tool')}: {source.get('evidence', '')}")
        paragraph(f"Remediation: {finding.get('recommendation', '')}")
    if not result.get("findings"):
        paragraph("No issues were reported by the completed tools.")
    paragraph("Observations", "Heading2")
    for observation in result.get("observations", []):
        paragraph(f"{observation.get('tool')}: {observation.get('title')} {observation.get('description', '')}")
    document.build(story)
    return output.getvalue()
