export function scanProgress(scan: { completed_tools: number; total_tools: number }): number {
  return scan.total_tools > 0 ? Math.max(0, Math.min(100, Math.round(100 * scan.completed_tools / scan.total_tools))) : 0;
}

export function isActiveScan(scan: { status: string } | null): boolean {
  return scan?.status === "queued" || scan?.status === "running";
}

export function scanAnnouncement(
  scan: { completed_tools: number; total_tools: number },
  labels: { status: string; tool?: string; completedTools: string },
): string {
  const tool = labels.tool ? ` · ${labels.tool}` : "";
  return `${labels.status}${tool}. ${labels.completedTools}: ${scan.completed_tools}/${scan.total_tools}`;
}
