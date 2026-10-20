import { type ScanStatus } from "@/lib/api";
import { scanAnnouncement, scanProgress } from "@/lib/scan-state";
import { useLanguage } from "@/contexts/LanguageContext";

const statusStyles: Record<ScanStatus["status"], string> = {
  queued: "text-warning", running: "text-primary", finished: "text-success", error: "text-destructive",
};

export default function ScanProgress({ scan }: { scan: ScanStatus }) {
  const { t } = useLanguage();
  const announcement = scanAnnouncement(scan, {
    status: t[scan.status],
    tool: scan.current_tool ? t.tools[scan.current_tool].name : undefined,
    completedTools: t.completedTools,
  });
  return <div className="space-y-3">
    <p className="sr-only" role="status">{announcement}</p>
    <div className="flex flex-wrap justify-between gap-2 text-sm tabular-nums">
      <span className={statusStyles[scan.status]}>{t[scan.status]}{scan.current_tool ? ` · ${t.tools[scan.current_tool].name}` : ""}</span>
      <span>{t.completedTools}: {scan.completed_tools}/{scan.total_tools} · {scan.elapsed}s</span>
    </div>
    <progress className="h-2 w-full accent-primary" aria-label={t.completedTools} value={scanProgress(scan)} max={100} />
  </div>;
}
