# SecScan local API

Base URL: `http://127.0.0.1:5000/api`. The frontend uses `/api` through Vite.
There are no accounts, authentication cookies, tokens, or CSRF bootstrap calls.
All local clients share scan history. Old `/auth/*` endpoints return 404.

Requests with an Origin must match `FRONTEND_ORIGINS`; cross-site fetches are
rejected. HTTP Host values must identify localhost or loopback. Mutations require
`Content-Type: application/json`. These checks are browser safeguards, not login.

## Start a scan

`POST /scan/start` (alias: `POST /scan`)

```json
{"target": "http://127.0.0.1:8081/", "tools": ["nmap", "zap"]}
```

Returns 202 with `scan_id`, `status: "queued"`, `target`, and `tools`.
The target host must match `ALLOWED_SCAN_HOSTS` (or `*` for any authorized host).
Nmap accepts an IP or HTTP(S) URL. Web scanners require HTTP(S). Empty, duplicate,
or unknown tools, credentials in URLs, fragments, invalid ports, and malformed targets return 400.

Unavailable selected tools return 503 before creating a job. One scan runs at a
time; a busy worker returns 429 with `Retry-After: 5`.

## Read state and reports

| Method / route | Response |
| --- | --- |
| `GET /health` | `{"status":"ok","service":"secscan"}` |
| `GET /tools/status` | Availability per tool and `allowed_hosts` |
| `GET /scans` | `{"scans":[...]}`; newest 50 local records |
| `GET /scan/{id}/status` | State, target, tools, timestamps, progress, error |
| `GET /scan/{id}/results` | 202 while active; result JSON when complete; 409 if no result |
| `GET /scan/{id}/report?format=html` | HTML download |
| `GET /scan/{id}/report?format=pdf` | PDF download (default format) |

Unknown or malformed IDs return 404. Invalid report format returns 400;
unavailable report data returns 409. Errors use `{"error":"message"}`.

Job states are `queued`, `running`, `finished`, and `error`. Results have
`outcome: completed | partial | error`; inspect it even when a job is finished.
An interrupted job becomes an error on backend restart.

## Result fields

- `tools_selected`: requested tools.
- `tools_ran`: tools that completed successfully.
- `tool_results`: per-tool execution status, diagnostic message, finding count.
- `findings`: grouped issues with severity, URL, parameter, evidence, sources,
  recommendation, and confidence (`single-tool` or `corroborated`).
- `observations`: informational results, including Nmap services.
- `counts`, `total_findings`, `raw_finding_count`: grouped and original counts.
- `started_at`, `finished_at`, `duration_seconds`: timing.

Evidence is untrusted text. Escape it when displaying it. Automated reports do
not constitute manual verification.
