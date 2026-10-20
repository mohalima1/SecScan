export type ToolId = "zap" | "nmap" | "sqlmap" | "nikto";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type ScanStatus = {
  scan_id: string; target: string; tools: ToolId[];
  status: "queued" | "running" | "finished" | "error";
  elapsed: number; current_tool: ToolId | null;
  completed_tools: number; total_tools: number; error: string | null;
  created_at: number;
};
export type Source = {
  tool: ToolId; url?: string; parameter?: string; evidence?: string;
  source_confidence?: string; scanner_rule_id?: string; cwe_id?: string;
};
export type Finding = {
  id: string; title: string; severity: Severity; description: string;
  url: string; parameter: string; recommendation: string; status: "reported";
  confidence: "single-tool" | "corroborated"; tools: ToolId[]; sources: Source[];
};
export type ToolResult = {
  status: "completed" | "partial" | "error" | "timeout"; error?: string | null;
  finding_count: number;
};
export type ScanResult = {
  scan_id: string; target: string; timestamp: string; duration_seconds: number;
  outcome: "completed" | "partial" | "error"; total_findings: number; raw_finding_count: number;
  tools_selected: ToolId[]; tools_ran: ToolId[]; counts: Record<Severity, number>;
  findings: Finding[]; observations: Array<{ tool: ToolId; title: string; description?: string; service?: string; product?: string; version?: string }>;
  tool_results: Partial<Record<ToolId, ToolResult>>;
};
export type ToolStatus = {
  tools: Record<ToolId, { available: boolean; version?: string }>;
  allowed_hosts: string[];
};

const API_BASE = (import.meta.env?.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

async function checkedFetch(path: string, init?: RequestInit) {
  const response = await fetch(API_BASE + path, { ...init, credentials: "omit" });
  if (!response.ok) {
    const body: { error?: string } = await response.json().catch(() => ({}));
    throw new ApiError(body.error || `Request failed (HTTP ${response.status}).`, response.status);
  }
  return response;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const response = await checkedFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const data = await response.json();
  return data as T;
}

export const startScan = (target: string, tools: ToolId[]) => post<{ scan_id: string }>("/scan/start", { target, tools });
export async function getScanStatus(scanId: string, signal?: AbortSignal): Promise<ScanStatus> {
  return (await checkedFetch(`/scan/${encodeURIComponent(scanId)}/status`, { signal })).json();
}
export async function getScanResults(scanId: string, signal?: AbortSignal): Promise<ScanResult> {
  const response = await checkedFetch(`/scan/${encodeURIComponent(scanId)}/results`, { signal });
  if (response.status === 202) throw new ApiError("The scan is still running.", 409);
  return response.json();
}
export async function getHistory(signal?: AbortSignal): Promise<{ scans: ScanStatus[] }> {
  return (await checkedFetch("/scans", { signal })).json();
}
export async function getToolStatus(signal?: AbortSignal): Promise<ToolStatus> {
  return (await checkedFetch("/tools/status", { signal })).json();
}
export async function downloadReport(scanId: string, format: "html" | "pdf") {
  const response = await checkedFetch(`/scan/${encodeURIComponent(scanId)}/report?format=${format}`);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `secscan-${scanId}.${format}`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
